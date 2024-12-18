#include <lib/service/event.h>
#include <lib/base/estring.h>
#include <lib/base/encoding.h>
#include <lib/dvb/dvbtime.h>
#include <lib/dvb/idvb.h>
#include <lib/dvb/db.h>
#include <dvbsi++/event_information_section.h>
#include <dvbsi++/short_event_descriptor.h>
#include <dvbsi++/extended_event_descriptor.h>
#include <dvbsi++/linkage_descriptor.h>
#include <dvbsi++/component_descriptor.h>
#include <dvbsi++/content_descriptor.h>
#include <dvbsi++/parental_rating_descriptor.h>
#include <dvbsi++/content_identifier_descriptor.h>
#include <dvbsi++/private_data_specifier_descriptor.h>
#include <dvbsi++/descriptor_tag.h>
#include <dvbsi++/pdc_descriptor.h>
#include <lib/base/nconfig.h>

#include <sys/types.h>
#include <fcntl.h>

bool eServiceEvent::m_Debug = false;

// static members / methods
std::string eServiceEvent::m_language = "---";
std::string eServiceEvent::m_language_alternative = "---";

///////////////////////////

DEFINE_REF(eServiceEvent);
DEFINE_REF(eComponentData);
DEFINE_REF(eGenreData);
DEFINE_REF(eParentalData);
DEFINE_REF(eCridData);

std::string eServiceEvent::crid_scheme = "crid://";
int eServiceEvent::m_UTF8CorrectMode = 0;

std::string eServiceEvent::normalise_crid(std::string crid, ePtr<eDVBService> service)
{
	if ( !crid.empty() )
	{
		//std::transform(crid.begin(), crid.end(), crid.begin(), ::tolower);
		if ( crid[0] == '/' )
		{
			if ( service && !service->m_default_authority.empty() )
			{
				crid = service->m_default_authority + crid;
			}
			else
			{
				// Don't use a CRID if it needs a default
				// authority but it doesn't have one
				// ZZ return "";
				crid = "missing_authority" + crid;
			}
		}
		if ( crid.substr(0, crid_scheme.size()) != crid_scheme )
		{
			std::string crid_lower = crid;
			std::transform(crid_lower.begin(), crid_lower.end(), crid_lower.begin(), ::tolower);
			if ( crid_lower.substr(0, crid_scheme.size()) != crid_scheme )
			{
				crid = crid_scheme + crid;
			}
		}
	}
	return crid;
}

eServiceEvent::eServiceEvent():
	m_begin(0), m_duration(0), m_event_id(0)
{
}

/* search for the presence of language from given EIT event descriptors*/
bool eServiceEvent::loadLanguage(Event *evt, const std::string &lang, int tsidonid, int sid)
{
	bool retval=0;
	std::string language = lang;
	for (DescriptorConstIterator desc = evt->getDescriptors()->begin(); desc != evt->getDescriptors()->end(); ++desc)
	{
		switch ((*desc)->getTag())
		{
			case LINKAGE_DESCRIPTOR:
				m_linkage_services.clear();
				break;
			case SHORT_EVENT_DESCRIPTOR:
			{
				const ShortEventDescriptor *sed = (ShortEventDescriptor*)*desc;
				std::string cc = sed->getIso639LanguageCode();
				std::transform(cc.begin(), cc.end(), cc.begin(), tolower);
				int table=encodingHandler.getCountryCodeDefaultMapping(cc);
				if (language == "---" || language.find(cc) != std::string::npos)
				{
					/* stick to this language, avoid merging or mixing descriptors of different languages */
					language = cc;
					m_event_name += entitiesDecode(replace_all(replace_all(convertDVBUTF8(sed->getEventName(), table, tsidonid), "\n", " ",table), "\t", " ",table));
					m_short_description += entitiesDecode(convertDVBUTF8(sed->getText(), table, tsidonid));
					retval=1;
				}
				break;
			}
			case EXTENDED_EVENT_DESCRIPTOR:
			{
				const ExtendedEventDescriptor *eed = (ExtendedEventDescriptor*)*desc;
				std::string cc = eed->getIso639LanguageCode();
				std::transform(cc.begin(), cc.end(), cc.begin(), tolower);
				int table=encodingHandler.getCountryCodeDefaultMapping(cc);
				if (language == "---" || language.find(cc) != std::string::npos)
				{
					/* stick to this language, avoid merging or mixing descriptors of different languages */
					language = cc;
					/*
					 * Bit of a hack, some providers put the event description partly in the short descriptor,
					 * and the remainder in extended event descriptors.
					 * In that case, we cannot really treat short/extended description as separate descriptions.
					 * Unfortunately we cannot recognise this, but we'll use the length of the short description
					 * to guess whether we should concatenate both descriptions (without any spaces)
					 */
					if (m_extended_description.empty() && m_short_description.size() >= 180)
					{
						m_extended_description = m_short_description;
						m_short_description = "";
					}
					m_extended_description += entitiesDecode(convertDVBUTF8(eed->getText(), table, tsidonid));
					const ExtendedEventList *itemlist = eed->getItems();
					for (ExtendedEventConstIterator it = itemlist->begin(); it != itemlist->end(); ++it)
					{
						m_extended_description_items += '\n';
						m_extended_description_items += convertDVBUTF8((*it)->getItemDescription(), table, tsidonid);
						m_extended_description_items += ": ";
						m_extended_description_items += convertDVBUTF8((*it)->getItem(), table, tsidonid);
					}
					retval=1;
				}
				break;
			}
			default:
				break;
		}
	}
	if ( retval == 1 )
	{
		int tsid =(tsidonid >> 16) & 0xffff;
		int onid = tsidonid & 0xffff;
		m_series_crid = "";
		m_episode_crid = "";
		m_recommendation_crid = "";
		std::string channelName;
		ePtr<eDVBDB> db = eDVBDB::getInstance();
		for (DescriptorConstIterator desc = evt->getDescriptors()->begin(); desc != evt->getDescriptors()->end(); ++desc)
		{
			switch ((*desc)->getTag())
			{
				case COMPONENT_DESCRIPTOR:
				{
					const ComponentDescriptor *cp = (ComponentDescriptor*)*desc;
					eComponentData data;
					data.m_streamContent = cp->getStreamContent();
					data.m_componentType = cp->getComponentType();
					data.m_componentTag = cp->getComponentTag();
					data.m_iso639LanguageCode = cp->getIso639LanguageCode();
					std::transform(data.m_iso639LanguageCode.begin(), data.m_iso639LanguageCode.end(), data.m_iso639LanguageCode.begin(), tolower);
					int table=encodingHandler.getCountryCodeDefaultMapping(data.m_iso639LanguageCode);
					data.m_text = convertDVBUTF8(cp->getText(),table,tsidonid);
					m_component_data.push_back(data);
					break;
				}
				case LINKAGE_DESCRIPTOR:
				{
					const LinkageDescriptor  *ld = (LinkageDescriptor*)*desc;
					if ( ld->getLinkageType() == 0xB0 )
					{
						eServiceReferenceDVB dvb_ref;
						dvb_ref.type = eServiceReference::idDVB;
						dvb_ref.setServiceType(1);
						dvb_ref.setTransportStreamID(ld->getTransportStreamId());
						dvb_ref.setOriginalNetworkID(ld->getOriginalNetworkId());
						dvb_ref.setServiceID(ld->getServiceId());
						const PrivateDataByteVector *privateData = ld->getPrivateDataBytes();
						dvb_ref.name = convertDVBUTF8((const unsigned char*)&((*privateData)[0]), privateData->size(), 1, tsidonid);
						m_linkage_services.push_back(dvb_ref);
					}
					break;
				}
				case CONTENT_DESCRIPTOR:
				{
					const ContentDescriptor *cd = (ContentDescriptor *)*desc;
					const ContentClassificationList *con = cd->getClassifications();
					for (ContentClassificationConstIterator it = con->begin(); it != con->end(); ++it)
					{
						eGenreData data;
						data.m_level1 = (*it)->getContentNibbleLevel1();
						data.m_level2 = (*it)->getContentNibbleLevel2();
						data.m_user1  = (*it)->getUserNibble1();
						data.m_user2  = (*it)->getUserNibble2();
						m_genres.push_back(data);
					}
					break;
				}
				case CONTENT_IDENTIFIER_DESCRIPTOR:
				{
					eServiceReference ref = db->searchReference(tsid, onid, sid);
					ePtr<eDVBService> service;
					db->getService(*(eServiceReferenceDVB*) &ref, service);
					if(service)
						channelName = service->m_service_name;
					auto cridd = (ContentIdentifierDescriptor *)*desc;
					auto crid = cridd->getIdentifier();
					for (auto it = crid->begin(); it != crid->end(); ++it)
					{
						eCridData data;
				        data.m_type = (*it)->getType();
						data.m_location = (*it)->getLocation();
						if (data.m_location == 0)
						{
							//eDebug("[Event] crid %02x %01x %s %d <%.*s>", (*it)->getType(), (*it)->getLocation(), m_event_name.c_str(), (*it)->getLength(), (*it)->getLength(), (*it)->getBytes()->data());
							data.m_crid  = normalise_crid(std::string((char*)(*it)->getBytes()->data(), (*it)->getLength()), service);
							m_crids.push_back(data);
							if(eServiceEvent::m_Debug) {
								eDebug("[Event] crid %02x %01x %s %d <%s>", (*it)->getType(), (*it)->getLocation(), m_event_name.c_str(), (*it)->getLength(), data.m_crid.c_str());
								if (data.m_type == eCridData::EPISODE_AU || data.m_type == eCridData::EPISODE)
									m_episode_crid = data.m_crid;
								else if (data.m_type == eCridData::SERIES_AU || data.m_type == eCridData::SERIES)
									m_series_crid = data.m_crid;
								else if (data.m_type == eCridData::RECOMMENDATION_AU || data.m_type == eCridData::RECOMMENDATION)
									m_recommendation_crid = data.m_crid;
							}
						}
						else if (data.m_location == 1)
						{
							if(eServiceEvent::m_Debug)
								eDebug("[Event] crid references not supported %04x:%04x:%04x  %-18s  %s %02x %01x %d", onid, tsid, sid, channelName.c_str(), getBeginTimeString().c_str(), (*it)->getType(), (*it)->getLocation(), (*it)->getReference());
						}
						else
						{
							if(eServiceEvent::m_Debug)
								eDebug("[Event] crid unknown location %04x:%04x:%04x  %-18s  %s %02x %01x", onid, tsid, sid, channelName.c_str(), getBeginTimeString().c_str(), (*it)->getType(), (*it)->getLocation());
						}
					}
					break;
				}
				case PARENTAL_RATING_DESCRIPTOR:
				{
					const ParentalRatingDescriptor *prd = (ParentalRatingDescriptor *)*desc;
					const ParentalRatingList *par = prd->getParentalRatings();
					for (ParentalRatingConstIterator it = par->begin(); it != par->end(); ++it)
					{
						eParentalData data;

						data.m_country_code = (*it)->getCountryCode();
						data.m_rating = (*it)->getRating();
						/* OPENSPA [morser] hack for M+ - epg with parental_rating = 0 */
						if ( data.m_rating == 0)
						{
							std::string description = m_short_description + m_extended_description;
							std::size_t found1 = description.find("(+");
							if (found1!=std::string::npos)
							{
								std::size_t found2 = description.find(")",found1+1);
								if (found2!=std::string::npos)
								{
									std::string newstr = description.substr(found1+2,found2-found1+2);
									int r = std::stoi(newstr);
									data.m_rating = r-3;
								}
							}
						}
						/* ************************************************************ */
						m_ratings.push_back(data);
					}
					break;
				}
				case PDC_DESCRIPTOR:
				{
					const PdcDescriptor *pdcd = (PdcDescriptor *)*desc;
					m_pdc_pil = pdcd->getProgrammeIdentificationLabel();
					break;
				}
			}
		}
		if (eServiceEvent::m_Debug && (!m_episode_crid.empty() || !m_series_crid.empty() || !m_recommendation_crid.empty()))
		{
			eDebug("[Event] crid  %04x:%04x:%04x  %-18s  %s  %-49s  %-49s %s %s", onid, tsid, sid, channelName.c_str(), getBeginTimeString().c_str(), m_series_crid.c_str(), m_episode_crid.c_str(), m_recommendation_crid.c_str(), m_event_name.c_str());
		}
	}
	if ( m_extended_description.find(m_short_description) == 0 )
		m_short_description = "";

	if ( ! m_extended_description_items.empty() and eConfigManager::getConfigBoolValue("config.epg.items_in_event_ext_descr") )
	{
		m_extended_description += '\n';
		m_extended_description += m_extended_description_items;
		m_extended_description_items = "";
	}

	if(eServiceEvent::m_UTF8CorrectMode > 0)
	{
		if(m_event_name.size() > 0 && !isUTF8(m_event_name))
		{
			if(eServiceEvent::m_UTF8CorrectMode == 2)
				eDebug("[eServiceEvent] event name is not UTF8\nhex output:%s\nstr output:%s\n",string_to_hex(m_event_name).c_str(),m_event_name.c_str());
			m_event_name = repairUTF8(m_event_name.c_str(), m_event_name.size());
		}
		if(m_short_description.size() > 0 && !isUTF8(m_short_description))
		{
			if(eServiceEvent::m_UTF8CorrectMode == 2)
				eDebug("[eServiceEvent] short description is not UTF8\nhex output:%s\nstr output:%s\n",string_to_hex(m_short_description).c_str(),m_short_description.c_str());
			m_short_description = repairUTF8(m_short_description.c_str(), m_short_description.size());
		}
		if(m_extended_description.size() > 0 && !isUTF8(m_extended_description))
		{
			if(eServiceEvent::m_UTF8CorrectMode == 2)
				eDebug("[eServiceEvent] extended description is not UTF8\nhex output:%s\nstr output:%s\n",string_to_hex(m_extended_description).c_str(),m_extended_description.c_str());
			m_extended_description = repairUTF8(m_extended_description.c_str(), m_extended_description.size());
		}
	}

	return retval;
}

std::string eServiceEvent::entitiesDecode( std::string str ) {
    std::string subs[] = { "&semi;", "&amp;", "&quot;", "&apos;", "&lt;", "&gt;", "&colon;", "&equals;", "&excl;" };
    std::string reps[] = { ";", "&", "\"", "'", "<", ">", ":", "=", "!" };
    std::size_t found;
    for( int j = 0; j < 9; j++ ) {
        do {
            found = str.find( subs[ j ] );
            if( found != std::string::npos ) {
                str.replace( found, subs[ j ].length(), reps[ j ] );
            }
        } while( found != std::string::npos );
       
    }
    return str;
}

RESULT eServiceEvent::parseFrom(Event *evt, int tsidonid)
{
	return parseFrom(evt, tsidonid, 0);
}

RESULT eServiceEvent::parseFrom(Event *evt, int tsidonid, int sid)
{
	m_begin = parseDVBtime(evt->getStartTimeMjd(), evt->getStartTimeBcd());
	m_event_id = evt->getEventId();
	uint32_t duration = evt->getDuration();
	m_duration = fromBCD(duration>>16)*3600+fromBCD(duration>>8)*60+fromBCD(duration);
	uint8_t running_status = evt->getRunningStatus();
	m_running_status = running_status;
	if (m_language != "---" && loadLanguage(evt, m_language, tsidonid, sid))
		return 0;
	if (m_language_alternative != "---" && loadLanguage(evt, m_language_alternative, tsidonid, sid))
		return 0;
	if (loadLanguage(evt, "---", tsidonid, sid))
		return 0;
	return 0; //NOSONAR
}

RESULT eServiceEvent::parseFrom(ATSCEvent *evt)
{
	m_begin = evt->getStartTime() + (time_t)315964800; /* ATSC GPS system time epoch is 00:00 Jan 6th 1980 */
	m_event_id = evt->getEventId();
	m_duration = evt->getLengthInSeconds();
	m_event_name = evt->getTitle(m_language);
	if (m_event_name.empty()) m_event_name = evt->getTitle(m_language_alternative);
	if (m_event_name.empty()) m_event_name = evt->getTitle("");
	return 0;
}

RESULT eServiceEvent::parseFrom(const ExtendedTextTableSection *sct)
{
	m_short_description = convertDVBUTF8(sct->getMessage(m_language));
	if (m_short_description.empty()) m_short_description = convertDVBUTF8(sct->getMessage(m_language_alternative));
	if (m_short_description.empty()) m_short_description = convertDVBUTF8(sct->getMessage(""));
	return 0;
}

RESULT eServiceEvent::parseFrom(const std::string& filename, int tsidonid)
{
	return parseFrom(filename, tsidonid, 0);
}

RESULT eServiceEvent::parseFrom(const std::string& filename, int tsidonid, int sid)
{
	if (!filename.empty())
	{
		int fd = ::open( filename.c_str(), O_RDONLY );
		if ( fd > -1 )
		{
			uint8_t buf[4096];
			int rd = ::read(fd, buf, 4096);
			::close(fd);
			if ( rd > 12 /*EIT_LOOP_SIZE*/ )
			{
				Event ev(buf);
				parseFrom(&ev, tsidonid, sid);
				return 0;
			}
		}
	}
	return -1;
}

std::string eServiceEvent::getBeginTimeString() const
{
	tm t;
	localtime_r(&m_begin, &t);
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wformat-truncation"
	char tmp[13];
	snprintf(tmp, 13, "%02d.%02d, %02d:%02d",
		t.tm_mday, t.tm_mon+1,
		t.tm_hour, t.tm_min);
#pragma GCC diagnostic pop
	return std::string(tmp, 12);
}

RESULT eServiceEvent::getGenreData(ePtr<eGenreData> &dest) const
{
	std::list<eGenreData>::const_iterator it = m_genres.begin();
	for(;it != m_genres.end(); ++it) {
		dest = new eGenreData(*it);
		//  for now just return the first item on the list
		return 0;
	}
	dest = 0;
	return -1;
}

PyObject *eServiceEvent::getGenreDataList() const
{
	ePyObject ret = PyList_New(m_genres.size());
	int cnt=0;
	for (std::list<eGenreData>::const_iterator it(m_genres.begin()); it != m_genres.end(); ++it)
	{
		ePyObject tuple = PyTuple_New(4);
		PyTuple_SET_ITEM(tuple, 0, PyLong_FromLong(it->getLevel1()));
		PyTuple_SET_ITEM(tuple, 1, PyLong_FromLong(it->getLevel2()));
		PyTuple_SET_ITEM(tuple, 2, PyLong_FromLong(it->getUser1()));
		PyTuple_SET_ITEM(tuple, 3, PyLong_FromLong(it->getUser2()));
		PyList_SET_ITEM(ret, cnt++, tuple);
	}
	return ret;
}

RESULT eServiceEvent::getParentalData(ePtr<eParentalData> &dest) const
{
	std::list<eParentalData>::const_iterator it = m_ratings.begin();
	for(;it != m_ratings.end(); ++it) {
		dest = new eParentalData(*it);
		//  for now just return the first item on the list
		return 0;
	}
	dest = 0;
	return -1;
}

PyObject *eServiceEvent::getParentalDataList() const
{
	ePyObject ret = PyList_New(m_ratings.size());
	int cnt = 0;
	for (std::list<eParentalData>::const_iterator it(m_ratings.begin()); it != m_ratings.end(); ++it)
	{
		ePyObject tuple = PyTuple_New(2);
		PyTuple_SET_ITEM(tuple, 0, PyUnicode_FromString(it->getCountryCode().c_str()));
		PyTuple_SET_ITEM(tuple, 1, PyLong_FromLong(it->getRating()));
		PyList_SET_ITEM(ret, cnt++, tuple);
	}
	return ret;
}

PyObject *eServiceEvent::getCridData(int mask) const
{
	ePyObject ret = PyList_New(0);
	for (std::list<eCridData>::const_iterator it(m_crids.begin()); it != m_crids.end(); ++it)
	{
		int cridMatchType = it->getType();
		if (cridMatchType >= eCridData::EPISODE_AU && cridMatchType <= eCridData::RECOMMENDATION_AU)
			cridMatchType -= eCridData::OFFSET_AU;
		if ((1 << cridMatchType) & mask)
		{
			ePyObject tuple = PyTuple_New(3);
			PyTuple_SET_ITEM(tuple, 0, PyLong_FromLong(it->getType()));
			PyTuple_SET_ITEM(tuple, 1, PyLong_FromLong(it->getLocation()));
			PyTuple_SET_ITEM(tuple, 2, PyUnicode_FromString(it->getCrid().c_str()));
			PyList_Append(ret, tuple);
		}
	}
	return ret;
}

RESULT eServiceEvent::getComponentData(ePtr<eComponentData> &dest, int tagnum) const
{
	std::list<eComponentData>::const_iterator it =
		m_component_data.begin();
	for(;it != m_component_data.end(); ++it)
	{
		if ( it->m_componentTag == tagnum )
		{
			dest=new eComponentData(*it);
			return 0;
		}
	}
	dest = 0;
	return -1;
}

PyObject *eServiceEvent::getComponentDataList() const
{
	ePyObject ret = PyList_New(m_component_data.size());
	int cnt = 0;
	for (std::list<eComponentData>::const_iterator it(m_component_data.begin()); it != m_component_data.end(); ++it)
	{
		ePyObject tuple = PyTuple_New(5);
		PyTuple_SET_ITEM(tuple, 0, PyLong_FromLong(it->m_componentTag));
		PyTuple_SET_ITEM(tuple, 1, PyLong_FromLong(it->m_componentType));
		PyTuple_SET_ITEM(tuple, 2, PyLong_FromLong(it->m_streamContent));
		PyTuple_SET_ITEM(tuple, 3, PyUnicode_FromString(it->m_iso639LanguageCode.c_str()));
		PyTuple_SET_ITEM(tuple, 4, PyUnicode_FromString(it->m_text.c_str()));
		PyList_SET_ITEM(ret, cnt++, tuple);
	}
	return ret;
}

RESULT eServiceEvent::getLinkageService(eServiceReference &service, eServiceReference &parent, int num) const
{
	std::list<eServiceReference>::const_iterator it =
		m_linkage_services.begin();
	while( it != m_linkage_services.end() && num-- )
		++it;
	if ( it != m_linkage_services.end() )
	{
		service = *it;
		eServiceReferenceDVB &subservice = (eServiceReferenceDVB&) service;
		eServiceReferenceDVB &current = (eServiceReferenceDVB&) parent;
		subservice.setDVBNamespace(current.getDVBNamespace());
		if ( current.getParentTransportStreamID().get() )
		{
			subservice.setParentTransportStreamID( current.getParentTransportStreamID() );
			subservice.setParentServiceID( current.getParentServiceID() );
		}
		else
		{
			subservice.setParentTransportStreamID( current.getTransportStreamID() );
			subservice.setParentServiceID( current.getServiceID() );
		}
		if ( subservice.getParentTransportStreamID() == subservice.getTransportStreamID() &&
			subservice.getParentServiceID() == subservice.getServiceID() )
		{
			subservice.setParentTransportStreamID( eTransportStreamID(0) );
			subservice.setParentServiceID( eServiceID(0) );
		}
		return 0;
	}
	service.type = eServiceReference::idInvalid;
	return -1;
}

DEFINE_REF(eDebugClass);
