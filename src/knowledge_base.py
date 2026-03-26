from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
import re
from typing import Any

import pandas as pd

# Embedded fictional historical ticket knowledge base.
HISTORICAL_TICKET_KB = [
    {
        'ticket_id': 'KB-10000',
        'title': 'VPN sign-in succeeds but access fails',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN sign-in succeeds but access fails'],
        'root_cause': 'Stale MFA token preventing session establishment',
        'resolution_steps': 'Removed the stale device certificate, enrolled a new one, and confirmed tunnel establishment.',
        'resolution_summary': 'Removed the stale device certificate',
        'priority': 'high',
        'environment': 'Windows 11',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10001',
        'title': 'VPN client hangs on connection step',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN client hangs on connection step'],
        'root_cause': 'Expired tunnel profile on endpoint',
        'resolution_steps': 'Checked gateway health, failed over to the secondary node, then had the user reconnect successfully.',
        'resolution_summary': 'Checked gateway health',
        'priority': 'high',
        'environment': 'Remote',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10002',
        'title': 'VPN tunnel drops after sign-in',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN tunnel drops after sign-in'],
        'root_cause': 'Expired tunnel profile on endpoint',
        'resolution_steps': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity.',
        'resolution_summary': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity',
        'priority': 'medium',
        'environment': 'Windows 10',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10003',
        'title': 'User cannot connect to VPN',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['User cannot connect to VPN'],
        'root_cause': 'Stale MFA token preventing session establishment',
        'resolution_steps': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity.',
        'resolution_summary': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10004',
        'title': 'VPN client hangs on connection step',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN client hangs on connection step'],
        'root_cause': 'Expired tunnel profile on endpoint',
        'resolution_steps': 'Updated the VPN profile, cleared cached adapter settings, and restarted the endpoint network stack.',
        'resolution_summary': 'Updated the VPN profile',
        'priority': 'high',
        'environment': 'Remote',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10005',
        'title': 'VPN client hangs on connection step',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN client hangs on connection step'],
        'root_cause': 'Corrupted client cache after update',
        'resolution_steps': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity.',
        'resolution_summary': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity',
        'priority': 'high',
        'environment': 'Windows 11',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10006',
        'title': 'VPN client hangs on connection step',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN client hangs on connection step'],
        'root_cause': 'Stale MFA token preventing session establishment',
        'resolution_steps': 'Checked gateway health, failed over to the secondary node, then had the user reconnect successfully.',
        'resolution_summary': 'Checked gateway health',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10007',
        'title': 'VPN client hangs on connection step',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN client hangs on connection step'],
        'root_cause': 'Expired tunnel profile on endpoint',
        'resolution_steps': "Reset the user's VPN adapter, re-applied the client configuration, and confirmed stable sign-in.",
        'resolution_summary': "Reset the user's VPN adapter",
        'priority': 'medium',
        'environment': 'Remote',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10008',
        'title': 'Users report intermittent remote access failures',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['Users report intermittent remote access failures'],
        'root_cause': 'Stale MFA token preventing session establishment',
        'resolution_steps': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity.',
        'resolution_summary': 'Validated MFA logs and re-synced the user token; restarted the VPN client and re-tested connectivity',
        'priority': 'high',
        'environment': 'Windows 10',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10009',
        'title': 'User cannot connect to VPN',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['User cannot connect to VPN'],
        'root_cause': 'Certificate trust chain issue on the device',
        'resolution_steps': 'Rolled back the broken client update and installed the approved version; remote access was restored.',
        'resolution_summary': 'Rolled back the broken client update and installed the approved version; remote access was restored',
        'priority': 'high',
        'environment': 'Remote',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10010',
        'title': 'User cannot connect to VPN',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['User cannot connect to VPN'],
        'root_cause': 'Certificate trust chain issue on the device',
        'resolution_steps': 'Updated the VPN profile, cleared cached adapter settings, and restarted the endpoint network stack.',
        'resolution_summary': 'Updated the VPN profile',
        'priority': 'medium',
        'environment': 'Remote',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10011',
        'title': 'VPN client hangs on connection step',
        'category': 'network',
        'subcategory': 'vpn',
        'possible_system': 'Authentication / Network',
        'keywords': ['vpn', 'remote access', 'connect', 'mfa', 'auth'],
        'symptoms': ['VPN client hangs on connection step'],
        'root_cause': 'Corrupted client cache after update',
        'resolution_steps': 'Checked gateway health, failed over to the secondary node, then had the user reconnect successfully.',
        'resolution_summary': 'Checked gateway health',
        'priority': 'medium',
        'environment': 'Remote',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10100',
        'title': 'Shared mailbox is missing',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Shared mailbox is missing'],
        'root_cause': 'Cached shared mailbox permissions stale',
        'resolution_steps': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed.',
        'resolution_summary': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10101',
        'title': 'Outlook freezes on launch',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Outlook freezes on launch'],
        'root_cause': 'Authentication token expired in Office session',
        'resolution_steps': 'Created a new Outlook profile, removed the broken profile, and confirmed mailbox access.',
        'resolution_summary': 'Created a new Outlook profile',
        'priority': 'low',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10102',
        'title': 'Outlook keeps prompting for credentials',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Outlook keeps prompting for credentials'],
        'root_cause': 'Search index corruption on the endpoint',
        'resolution_steps': 'Rebuilt the local OST, restarted Outlook, and confirmed calendar/mail synchronization.',
        'resolution_summary': 'Rebuilt the local OST',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10103',
        'title': 'Outlook cannot open the mailbox',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Outlook cannot open the mailbox'],
        'root_cause': 'Autodiscover mismatch after mailbox move',
        'resolution_steps': 'Rebuilt the local OST, restarted Outlook, and confirmed calendar/mail synchronization.',
        'resolution_summary': 'Rebuilt the local OST',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10104',
        'title': 'Calendar does not sync',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Calendar does not sync'],
        'root_cause': 'OST file corruption after abrupt shutdown',
        'resolution_steps': 'Rebuilt the local OST, restarted Outlook, and confirmed calendar/mail synchronization.',
        'resolution_summary': 'Rebuilt the local OST',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10105',
        'title': 'Mail search returns incomplete results',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Mail search returns incomplete results'],
        'root_cause': 'Autodiscover mismatch after mailbox move',
        'resolution_steps': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed.',
        'resolution_summary': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed',
        'priority': 'low',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10106',
        'title': 'Mail search returns incomplete results',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Mail search returns incomplete results'],
        'root_cause': 'OST file corruption after abrupt shutdown',
        'resolution_steps': 'Corrected the autodiscover target and refreshed the account configuration successfully.',
        'resolution_summary': 'Corrected the autodiscover target and refreshed the account configuration successfully',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10107',
        'title': 'Outlook cannot open the mailbox',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Outlook cannot open the mailbox'],
        'root_cause': 'Cached shared mailbox permissions stale',
        'resolution_steps': 'Rebuilt the local OST, restarted Outlook, and confirmed calendar/mail synchronization.',
        'resolution_summary': 'Rebuilt the local OST',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10108',
        'title': 'Outlook freezes on launch',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Outlook freezes on launch'],
        'root_cause': 'Search index corruption on the endpoint',
        'resolution_steps': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed.',
        'resolution_summary': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed',
        'priority': 'low',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10109',
        'title': 'Outlook freezes on launch',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Outlook freezes on launch'],
        'root_cause': 'OST file corruption after abrupt shutdown',
        'resolution_steps': 'Rebuilt the Windows search index and ran an Office quick repair; search returned to normal.',
        'resolution_summary': 'Rebuilt the Windows search index and ran an Office quick repair; search returned to normal',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10110',
        'title': 'Shared mailbox is missing',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Shared mailbox is missing'],
        'root_cause': 'Cached shared mailbox permissions stale',
        'resolution_steps': 'Signed out of Office, cleared stored credentials, signed in again, and verified mail flow.',
        'resolution_summary': 'Signed out of Office',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10111',
        'title': 'Outlook cannot open the mailbox',
        'category': 'messaging',
        'subcategory': 'outlook',
        'possible_system': 'Email System',
        'keywords': ['outlook', 'mailbox', 'calendar', 'mail', 'exchange'],
        'symptoms': ['Outlook cannot open the mailbox'],
        'root_cause': 'Authentication token expired in Office session',
        'resolution_steps': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed.',
        'resolution_summary': 'Removed and re-added the shared mailbox after reapplying permissions; sync resumed',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10200',
        'title': 'Zoom room controller is offline',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Zoom room controller is offline'],
        'root_cause': 'Room calendar sync failed and meeting metadata was missing',
        'resolution_steps': 'Forced a calendar re-sync, validated room mailbox permissions, and restored scheduled meeting visibility.',
        'resolution_summary': 'Forced a calendar re-sync',
        'priority': 'medium',
        'environment': 'Zoom Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10201',
        'title': 'Zoom room controller is offline',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Zoom room controller is offline'],
        'root_cause': 'Room calendar sync failed and meeting metadata was missing',
        'resolution_steps': 'Updated the Zoom Rooms client to the approved version and re-tested join, share, and camera features.',
        'resolution_summary': 'Updated the Zoom Rooms client to the approved version and re-tested join',
        'priority': 'high',
        'environment': 'Zoom Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10202',
        'title': 'Zoom room controller is offline',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Zoom room controller is offline'],
        'root_cause': 'Outdated Zoom Rooms client on the room system',
        'resolution_steps': 'Changed the active microphone/speaker selection, restarted Zoom Rooms, and confirmed audio in both directions.',
        'resolution_summary': 'Changed the active microphone/speaker selection',
        'priority': 'high',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10203',
        'title': 'Meeting room display shows the wrong layout',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Meeting room display shows the wrong layout'],
        'root_cause': 'Room calendar sync failed and meeting metadata was missing',
        'resolution_steps': 'Reconnected the USB video path, reselected the camera in room settings, and verified the video feed.',
        'resolution_summary': 'Reconnected the USB video path',
        'priority': 'medium',
        'environment': 'Zoom Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10204',
        'title': 'Camera is not detected in Zoom',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Camera is not detected in Zoom'],
        'root_cause': 'USB camera path disconnected after device reboot',
        'resolution_steps': 'Reconnected the USB video path, reselected the camera in room settings, and verified the video feed.',
        'resolution_summary': 'Reconnected the USB video path',
        'priority': 'medium',
        'environment': 'Zoom Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10205',
        'title': 'Zoom room controller is offline',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Zoom room controller is offline'],
        'root_cause': 'Outdated Zoom Rooms client on the room system',
        'resolution_steps': 'Reconnected the USB video path, reselected the camera in room settings, and verified the video feed.',
        'resolution_summary': 'Reconnected the USB video path',
        'priority': 'high',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10206',
        'title': 'Zoom room has no audio',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Zoom room has no audio'],
        'root_cause': 'USB camera path disconnected after device reboot',
        'resolution_steps': 'Forced a calendar re-sync, validated room mailbox permissions, and restored scheduled meeting visibility.',
        'resolution_summary': 'Forced a calendar re-sync',
        'priority': 'high',
        'environment': 'Conference Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10207',
        'title': 'Screen sharing fails in the conference room',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Screen sharing fails in the conference room'],
        'root_cause': 'Audio device selected incorrectly after update',
        'resolution_steps': 'Reconnected the USB video path, reselected the camera in room settings, and verified the video feed.',
        'resolution_summary': 'Reconnected the USB video path',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10208',
        'title': 'Meeting room display shows the wrong layout',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Meeting room display shows the wrong layout'],
        'root_cause': 'Outdated Zoom Rooms client on the room system',
        'resolution_steps': 'Forced a calendar re-sync, validated room mailbox permissions, and restored scheduled meeting visibility.',
        'resolution_summary': 'Forced a calendar re-sync',
        'priority': 'high',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10209',
        'title': 'Zoom room controller is offline',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Zoom room controller is offline'],
        'root_cause': 'Room controller lost pairing with the room appliance',
        'resolution_steps': 'Forced a calendar re-sync, validated room mailbox permissions, and restored scheduled meeting visibility.',
        'resolution_summary': 'Forced a calendar re-sync',
        'priority': 'high',
        'environment': 'Zoom Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10210',
        'title': 'Camera is not detected in Zoom',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Camera is not detected in Zoom'],
        'root_cause': 'Room controller lost pairing with the room appliance',
        'resolution_steps': 'Reconnected the USB video path, reselected the camera in room settings, and verified the video feed.',
        'resolution_summary': 'Reconnected the USB video path',
        'priority': 'high',
        'environment': 'Zoom Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10211',
        'title': 'Zoom room has no audio',
        'category': 'collaboration',
        'subcategory': 'zoom',
        'possible_system': 'Collaboration / Meetings',
        'keywords': ['zoom', 'meeting', 'camera', 'audio', 'mic', 'room'],
        'symptoms': ['Zoom room has no audio'],
        'root_cause': 'Audio device selected incorrectly after update',
        'resolution_steps': 'Updated the Zoom Rooms client to the approved version and re-tested join, share, and camera features.',
        'resolution_summary': 'Updated the Zoom Rooms client to the approved version and re-tested join',
        'priority': 'medium',
        'environment': 'Zoom Room',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10300',
        'title': 'User cannot print to the office printer',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['User cannot print to the office printer'],
        'root_cause': 'Device mapped to retired print queue',
        'resolution_steps': 'Re-authenticated the user to the secure print service and confirmed badge release works.',
        'resolution_summary': 'Re-authenticated the user to the secure print service and confirmed badge release works',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10301',
        'title': 'Printer appears offline on the endpoint',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Printer appears offline on the endpoint'],
        'root_cause': 'Stuck print spooler service on the endpoint',
        'resolution_steps': 'Restarted the print spooler, cleared the queue, and resent the print job successfully.',
        'resolution_summary': 'Restarted the print spooler',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10302',
        'title': 'Secure print release fails',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Secure print release fails'],
        'root_cause': 'Embedded print release service unreachable',
        'resolution_steps': 'Removed the outdated driver, installed the approved queue package, and validated test printing.',
        'resolution_summary': 'Removed the outdated driver',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10303',
        'title': 'Badge release at printer does not work',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Badge release at printer does not work'],
        'root_cause': 'Stuck print spooler service on the endpoint',
        'resolution_steps': 'Restarted the print spooler, cleared the queue, and resent the print job successfully.',
        'resolution_summary': 'Restarted the print spooler',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10304',
        'title': 'Badge release at printer does not work',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Badge release at printer does not work'],
        'root_cause': 'Printer queue corruption on the print server',
        'resolution_steps': 'Removed the outdated driver, installed the approved queue package, and validated test printing.',
        'resolution_summary': 'Removed the outdated driver',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10305',
        'title': 'User cannot print to the office printer',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['User cannot print to the office printer'],
        'root_cause': 'Embedded print release service unreachable',
        'resolution_steps': 'Removed the outdated driver, installed the approved queue package, and validated test printing.',
        'resolution_summary': 'Removed the outdated driver',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10306',
        'title': 'Large PDF prints as blank pages',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Large PDF prints as blank pages'],
        'root_cause': 'Broken secure print authentication token',
        'resolution_steps': 'Mapped the endpoint to the active queue and removed the retired printer object.',
        'resolution_summary': 'Mapped the endpoint to the active queue and removed the retired printer object',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10307',
        'title': 'Printer appears offline on the endpoint',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Printer appears offline on the endpoint'],
        'root_cause': 'Driver mismatch after Windows update',
        'resolution_steps': 'Re-authenticated the user to the secure print service and confirmed badge release works.',
        'resolution_summary': 'Re-authenticated the user to the secure print service and confirmed badge release works',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10308',
        'title': 'Large PDF prints as blank pages',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Large PDF prints as blank pages'],
        'root_cause': 'Stuck print spooler service on the endpoint',
        'resolution_steps': 'Validated printer connectivity, restarted the release service, and verified user authentication flow.',
        'resolution_summary': 'Validated printer connectivity',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10309',
        'title': 'Secure print release fails',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Secure print release fails'],
        'root_cause': 'Driver mismatch after Windows update',
        'resolution_steps': 'Re-authenticated the user to the secure print service and confirmed badge release works.',
        'resolution_summary': 'Re-authenticated the user to the secure print service and confirmed badge release works',
        'priority': 'medium',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10310',
        'title': 'Printer appears offline on the endpoint',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Printer appears offline on the endpoint'],
        'root_cause': 'Broken secure print authentication token',
        'resolution_steps': 'Re-authenticated the user to the secure print service and confirmed badge release works.',
        'resolution_summary': 'Re-authenticated the user to the secure print service and confirmed badge release works',
        'priority': 'medium',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10311',
        'title': 'Secure print release fails',
        'category': 'printing',
        'subcategory': 'printer',
        'possible_system': 'Printing / Endpoint',
        'keywords': ['printer', 'print', 'badge', 'queue', 'spooler', 'auth'],
        'symptoms': ['Secure print release fails'],
        'root_cause': 'Device mapped to retired print queue',
        'resolution_steps': 'Cleared the print server queue, restarted the service, and confirmed jobs were processed normally.',
        'resolution_summary': 'Cleared the print server queue',
        'priority': 'medium',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10400',
        'title': 'Laptop is very slow after startup',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Laptop is very slow after startup'],
        'root_cause': 'Endpoint security scan stuck on a large file set',
        'resolution_steps': 'Disabled unnecessary startup apps and confirmed faster sign-in and lower steady-state load.',
        'resolution_summary': 'Disabled unnecessary startup apps and confirmed faster sign-in and lower steady-state load',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10401',
        'title': 'Logon takes much longer than normal',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Logon takes much longer than normal'],
        'root_cause': 'Startup application load too high',
        'resolution_steps': 'Freed disk space, cleaned temp files, and rebooted the device to restore responsiveness.',
        'resolution_summary': 'Freed disk space',
        'priority': 'medium',
        'environment': 'Laptop',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10402',
        'title': 'Application freezes because memory is exhausted',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Application freezes because memory is exhausted'],
        'root_cause': 'Heavy background process after software update',
        'resolution_steps': 'Stopped the stuck security scan, rescheduled it, and confirmed CPU returned to normal.',
        'resolution_summary': 'Stopped the stuck security scan',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10403',
        'title': 'Device becomes slow after VPN connects',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Device becomes slow after VPN connects'],
        'root_cause': 'Runaway browser or meeting client process',
        'resolution_steps': 'Freed disk space, cleaned temp files, and rebooted the device to restore responsiveness.',
        'resolution_summary': 'Freed disk space',
        'priority': 'low',
        'environment': 'Laptop',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10404',
        'title': 'Fan runs constantly and system lags',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Fan runs constantly and system lags'],
        'root_cause': 'Startup application load too high',
        'resolution_steps': 'Identified the high-usage process, restarted it, and installed the pending app update.',
        'resolution_summary': 'Identified the high-usage process',
        'priority': 'medium',
        'environment': 'Laptop',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10405',
        'title': 'Logon takes much longer than normal',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Logon takes much longer than normal'],
        'root_cause': 'Heavy background process after software update',
        'resolution_steps': 'Cleared corrupted cache data and rebuilt indexing in a controlled maintenance window.',
        'resolution_summary': 'Cleared corrupted cache data and rebuilt indexing in a controlled maintenance window',
        'priority': 'low',
        'environment': 'Laptop',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10406',
        'title': 'Logon takes much longer than normal',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Logon takes much longer than normal'],
        'root_cause': 'Runaway browser or meeting client process',
        'resolution_steps': 'Disabled unnecessary startup apps and confirmed faster sign-in and lower steady-state load.',
        'resolution_summary': 'Disabled unnecessary startup apps and confirmed faster sign-in and lower steady-state load',
        'priority': 'low',
        'environment': 'Laptop',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10407',
        'title': 'Logon takes much longer than normal',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Logon takes much longer than normal'],
        'root_cause': 'Endpoint security scan stuck on a large file set',
        'resolution_steps': 'Identified the high-usage process, restarted it, and installed the pending app update.',
        'resolution_summary': 'Identified the high-usage process',
        'priority': 'medium',
        'environment': 'Laptop',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10408',
        'title': 'Device becomes slow after VPN connects',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Device becomes slow after VPN connects'],
        'root_cause': 'Corrupt temp and cache files causing repeated indexing',
        'resolution_steps': 'Identified the high-usage process, restarted it, and installed the pending app update.',
        'resolution_summary': 'Identified the high-usage process',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10409',
        'title': 'High CPU usage makes the device unusable',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['High CPU usage makes the device unusable'],
        'root_cause': 'Heavy background process after software update',
        'resolution_steps': 'Stopped the stuck security scan, rescheduled it, and confirmed CPU returned to normal.',
        'resolution_summary': 'Stopped the stuck security scan',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10410',
        'title': 'Fan runs constantly and system lags',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Fan runs constantly and system lags'],
        'root_cause': 'Startup application load too high',
        'resolution_steps': 'Disabled unnecessary startup apps and confirmed faster sign-in and lower steady-state load.',
        'resolution_summary': 'Disabled unnecessary startup apps and confirmed faster sign-in and lower steady-state load',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10411',
        'title': 'Fan runs constantly and system lags',
        'category': 'endpoint',
        'subcategory': 'performance',
        'possible_system': 'Endpoint / Device Performance',
        'keywords': ['laptop', 'slow', 'cpu', 'memory', 'performance', 'device'],
        'symptoms': ['Fan runs constantly and system lags'],
        'root_cause': 'Startup application load too high',
        'resolution_steps': 'Stopped the stuck security scan, rescheduled it, and confirmed CPU returned to normal.',
        'resolution_summary': 'Stopped the stuck security scan',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10500',
        'title': 'SSO login fails after password change',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['SSO login fails after password change'],
        'root_cause': 'SSO token cache invalid after credential change',
        'resolution_steps': 'Reviewed sign-in logs, cleared stale sessions, and confirmed successful login.',
        'resolution_summary': 'Reviewed sign-in logs',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10501',
        'title': 'Account is locked out repeatedly',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['Account is locked out repeatedly'],
        'root_cause': 'MFA push blocked by policy mismatch',
        'resolution_steps': 'Reviewed sign-in logs, cleared stale sessions, and confirmed successful login.',
        'resolution_summary': 'Reviewed sign-in logs',
        'priority': 'high',
        'environment': 'Cloud',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10502',
        'title': 'MFA prompt never arrives',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['MFA prompt never arrives'],
        'root_cause': 'Account lockout caused by old mobile client',
        'resolution_steps': 'Found the device repeatedly submitting the old password, removed cached credentials, and unlocked the account.',
        'resolution_summary': 'Found the device repeatedly submitting the old password',
        'priority': 'high',
        'environment': 'Hybrid',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10503',
        'title': 'User receives access denied despite correct credentials',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['User receives access denied despite correct credentials'],
        'root_cause': 'Conditional access policy too restrictive',
        'resolution_steps': 'Found the device repeatedly submitting the old password, removed cached credentials, and unlocked the account.',
        'resolution_summary': 'Found the device repeatedly submitting the old password',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10504',
        'title': 'Password reset does not propagate',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['Password reset does not propagate'],
        'root_cause': 'SSO token cache invalid after credential change',
        'resolution_steps': 'Adjusted the conditional access assignment and confirmed the user could sign in.',
        'resolution_summary': 'Adjusted the conditional access assignment and confirmed the user could sign in',
        'priority': 'high',
        'environment': 'Cloud',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10505',
        'title': 'User receives access denied despite correct credentials',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['User receives access denied despite correct credentials'],
        'root_cause': 'MFA push blocked by policy mismatch',
        'resolution_steps': 'Adjusted the conditional access assignment and confirmed the user could sign in.',
        'resolution_summary': 'Adjusted the conditional access assignment and confirmed the user could sign in',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10506',
        'title': 'Account is locked out repeatedly',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['Account is locked out repeatedly'],
        'root_cause': 'Account lockout caused by old mobile client',
        'resolution_steps': 'Reviewed sign-in logs, cleared stale sessions, and confirmed successful login.',
        'resolution_summary': 'Reviewed sign-in logs',
        'priority': 'medium',
        'environment': 'Cloud',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10507',
        'title': 'Account is locked out repeatedly',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['Account is locked out repeatedly'],
        'root_cause': 'Conditional access policy too restrictive',
        'resolution_steps': 'Adjusted the conditional access assignment and confirmed the user could sign in.',
        'resolution_summary': 'Adjusted the conditional access assignment and confirmed the user could sign in',
        'priority': 'medium',
        'environment': 'Cloud',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10508',
        'title': 'MFA prompt never arrives',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['MFA prompt never arrives'],
        'root_cause': 'SSO token cache invalid after credential change',
        'resolution_steps': 'Adjusted the conditional access assignment and confirmed the user could sign in.',
        'resolution_summary': 'Adjusted the conditional access assignment and confirmed the user could sign in',
        'priority': 'high',
        'environment': 'Cloud',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10509',
        'title': 'User receives access denied despite correct credentials',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['User receives access denied despite correct credentials'],
        'root_cause': 'Stale credentials stored on a mapped device or service',
        'resolution_steps': 'Found the device repeatedly submitting the old password, removed cached credentials, and unlocked the account.',
        'resolution_summary': 'Found the device repeatedly submitting the old password',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10510',
        'title': 'User cannot log in to the company portal',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['User cannot log in to the company portal'],
        'root_cause': 'Stale credentials stored on a mapped device or service',
        'resolution_steps': 'Adjusted the conditional access assignment and confirmed the user could sign in.',
        'resolution_summary': 'Adjusted the conditional access assignment and confirmed the user could sign in',
        'priority': 'high',
        'environment': 'Cloud',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10511',
        'title': 'User cannot log in to the company portal',
        'category': 'identity',
        'subcategory': 'authentication',
        'possible_system': 'Identity / Access',
        'keywords': ['login', 'password', 'mfa', 'lockout', 'authentication', 'access'],
        'symptoms': ['User cannot log in to the company portal'],
        'root_cause': 'Conditional access policy too restrictive',
        'resolution_steps': 'Validated MFA enrollment and push delivery, then re-registered the user token.',
        'resolution_summary': 'Validated MFA enrollment and push delivery',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'high',
    },
    {
        'ticket_id': 'KB-10600',
        'title': 'Wi-Fi drops when moving between rooms',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Wi-Fi drops when moving between rooms'],
        'root_cause': 'Local adapter driver issue after update',
        'resolution_steps': 'Adjusted roaming sensitivity and confirmed stable handoff across office areas.',
        'resolution_summary': 'Adjusted roaming sensitivity and confirmed stable handoff across office areas',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10601',
        'title': 'Wireless connection is very slow',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Wireless connection is very slow'],
        'root_cause': 'DHCP renewal failure after reconnect',
        'resolution_steps': 'Adjusted roaming sensitivity and confirmed stable handoff across office areas.',
        'resolution_summary': 'Adjusted roaming sensitivity and confirmed stable handoff across office areas',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10602',
        'title': 'Wireless connection is very slow',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Wireless connection is very slow'],
        'root_cause': '802.1X authentication failure',
        'resolution_steps': 'Updated the wireless driver, reset the adapter, and verified throughput returned to expected levels.',
        'resolution_summary': 'Updated the wireless driver',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10603',
        'title': 'Wi-Fi drops when moving between rooms',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Wi-Fi drops when moving between rooms'],
        'root_cause': '802.1X authentication failure',
        'resolution_steps': 'Renewed the device certificate and confirmed wireless authentication completed successfully.',
        'resolution_summary': 'Renewed the device certificate and confirmed wireless authentication completed successfully',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10604',
        'title': 'Wireless connection is very slow',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Wireless connection is very slow'],
        'root_cause': '802.1X authentication failure',
        'resolution_steps': 'Removed and re-added the wireless profile, then confirmed stable connection to the corporate SSID.',
        'resolution_summary': 'Removed and re-added the wireless profile',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10605',
        'title': 'User cannot join the corporate SSID',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['User cannot join the corporate SSID'],
        'root_cause': 'Saved profile mismatch after SSID settings change',
        'resolution_steps': 'Updated the wireless driver, reset the adapter, and verified throughput returned to expected levels.',
        'resolution_summary': 'Updated the wireless driver',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10606',
        'title': 'User cannot join the corporate SSID',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['User cannot join the corporate SSID'],
        'root_cause': 'Weak roaming between access points',
        'resolution_steps': 'Reviewed 802.1X logs, corrected the supplicant settings, and restored access.',
        'resolution_summary': 'Reviewed 802.1X logs',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10607',
        'title': 'Laptop disconnects from office Wi-Fi',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Laptop disconnects from office Wi-Fi'],
        'root_cause': '802.1X authentication failure',
        'resolution_steps': 'Reviewed 802.1X logs, corrected the supplicant settings, and restored access.',
        'resolution_summary': 'Reviewed 802.1X logs',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10608',
        'title': 'Wireless connection is very slow',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Wireless connection is very slow'],
        'root_cause': 'Weak roaming between access points',
        'resolution_steps': 'Forced DHCP renewal after adapter reset and confirmed internet connectivity was restored.',
        'resolution_summary': 'Forced DHCP renewal after adapter reset and confirmed internet connectivity was restored',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10609',
        'title': 'Wi-Fi drops when moving between rooms',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['Wi-Fi drops when moving between rooms'],
        'root_cause': 'Stale wireless certificate',
        'resolution_steps': 'Reviewed 802.1X logs, corrected the supplicant settings, and restored access.',
        'resolution_summary': 'Reviewed 802.1X logs',
        'priority': 'medium',
        'environment': 'Laptop',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10610',
        'title': 'User cannot join the corporate SSID',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['User cannot join the corporate SSID'],
        'root_cause': 'Saved profile mismatch after SSID settings change',
        'resolution_steps': 'Forced DHCP renewal after adapter reset and confirmed internet connectivity was restored.',
        'resolution_summary': 'Forced DHCP renewal after adapter reset and confirmed internet connectivity was restored',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10611',
        'title': 'User cannot join the corporate SSID',
        'category': 'network',
        'subcategory': 'wifi',
        'possible_system': 'Wireless / Network',
        'keywords': ['wifi', 'wireless', 'ssid', 'roaming', 'signal', 'network'],
        'symptoms': ['User cannot join the corporate SSID'],
        'root_cause': 'Local adapter driver issue after update',
        'resolution_steps': 'Reviewed 802.1X logs, corrected the supplicant settings, and restored access.',
        'resolution_summary': 'Reviewed 802.1X logs',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10700',
        'title': 'Mapped drive is missing',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['Mapped drive is missing'],
        'root_cause': 'VPN dependency missing for offsite access',
        'resolution_steps': 'Updated shortcuts to the current DFS target and confirmed file access.',
        'resolution_summary': 'Updated shortcuts to the current DFS target and confirmed file access',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10701',
        'title': 'Mapped drive is missing',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['Mapped drive is missing'],
        'root_cause': 'Drive mapping script failed at sign-in',
        'resolution_steps': 'Validated share permissions and restored the required access group membership.',
        'resolution_summary': 'Validated share permissions and restored the required access group membership',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10702',
        'title': 'Shared folder opens slowly',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['Shared folder opens slowly'],
        'root_cause': 'DFS path update not reflected in shortcut',
        'resolution_steps': 'Re-ran the mapping script, corrected the path, and confirmed the drive reappeared.',
        'resolution_summary': 'Re-ran the mapping script',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10703',
        'title': 'User gets access denied to file share',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['User gets access denied to file share'],
        'root_cause': 'VPN dependency missing for offsite access',
        'resolution_steps': 'Cleared cached SMB credentials and remapped the drive successfully.',
        'resolution_summary': 'Cleared cached SMB credentials and remapped the drive successfully',
        'priority': 'medium',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10704',
        'title': 'User gets access denied to file share',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['User gets access denied to file share'],
        'root_cause': 'Offline files conflict on the endpoint',
        'resolution_steps': 'Resolved the offline files conflict and confirmed normal save and open operations.',
        'resolution_summary': 'Resolved the offline files conflict and confirmed normal save and open operations',
        'priority': 'medium',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10705',
        'title': 'Shared folder opens slowly',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['Shared folder opens slowly'],
        'root_cause': 'Drive mapping script failed at sign-in',
        'resolution_steps': 'Updated shortcuts to the current DFS target and confirmed file access.',
        'resolution_summary': 'Updated shortcuts to the current DFS target and confirmed file access',
        'priority': 'low',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10706',
        'title': 'User gets access denied to file share',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['User gets access denied to file share'],
        'root_cause': 'VPN dependency missing for offsite access',
        'resolution_steps': 'Re-ran the mapping script, corrected the path, and confirmed the drive reappeared.',
        'resolution_summary': 'Re-ran the mapping script',
        'priority': 'medium',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10707',
        'title': 'User cannot save files to shared drive',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['User cannot save files to shared drive'],
        'root_cause': 'Drive mapping script failed at sign-in',
        'resolution_steps': 'Updated shortcuts to the current DFS target and confirmed file access.',
        'resolution_summary': 'Updated shortcuts to the current DFS target and confirmed file access',
        'priority': 'low',
        'environment': 'Hybrid',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10708',
        'title': 'User gets access denied to file share',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['User gets access denied to file share'],
        'root_cause': 'Drive mapping script failed at sign-in',
        'resolution_steps': 'Updated shortcuts to the current DFS target and confirmed file access.',
        'resolution_summary': 'Updated shortcuts to the current DFS target and confirmed file access',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10709',
        'title': 'Mapped drive is missing',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['Mapped drive is missing'],
        'root_cause': 'DFS path update not reflected in shortcut',
        'resolution_steps': 'Resolved the offline files conflict and confirmed normal save and open operations.',
        'resolution_summary': 'Resolved the offline files conflict and confirmed normal save and open operations',
        'priority': 'medium',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10710',
        'title': 'Shortcut to network share no longer works',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['Shortcut to network share no longer works'],
        'root_cause': 'Permissions changed on the target share',
        'resolution_steps': 'Re-ran the mapping script, corrected the path, and confirmed the drive reappeared.',
        'resolution_summary': 'Re-ran the mapping script',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10711',
        'title': 'User gets access denied to file share',
        'category': 'storage',
        'subcategory': 'file_share',
        'possible_system': 'File Services / Access',
        'keywords': ['share', 'drive', 'mapped drive', 'file share', 'access denied'],
        'symptoms': ['User gets access denied to file share'],
        'root_cause': 'DFS path update not reflected in shortcut',
        'resolution_steps': 'Re-ran the mapping script, corrected the path, and confirmed the drive reappeared.',
        'resolution_summary': 'Re-ran the mapping script',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10800',
        'title': 'Monitor flickers intermittently',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Monitor flickers intermittently'],
        'root_cause': 'USB-C dock negotiation failure',
        'resolution_steps': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized.',
        'resolution_summary': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10801',
        'title': 'Display resolution is wrong after docking',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Display resolution is wrong after docking'],
        'root_cause': 'Power delivery instability through the dock',
        'resolution_steps': 'Tested with a known-good cable and port, then replaced the failing cable.',
        'resolution_summary': 'Tested with a known-good cable and port',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10802',
        'title': 'Monitor flickers intermittently',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Monitor flickers intermittently'],
        'root_cause': 'Dock firmware outdated',
        'resolution_steps': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized.',
        'resolution_summary': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized',
        'priority': 'low',
        'environment': 'Docking Station',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10803',
        'title': 'Second monitor is not detected',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Second monitor is not detected'],
        'root_cause': 'USB-C dock negotiation failure',
        'resolution_steps': 'Power-cycled the dock and reinitialized USB-C negotiation; external display returned.',
        'resolution_summary': 'Power-cycled the dock and reinitialized USB-C negotiation; external display returned',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10804',
        'title': 'Display resolution is wrong after docking',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Display resolution is wrong after docking'],
        'root_cause': 'Display cable path seated incorrectly',
        'resolution_steps': 'Reset display settings, switched to extend mode, and saved the new layout.',
        'resolution_summary': 'Reset display settings',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10805',
        'title': 'External screen stays black after wake',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['External screen stays black after wake'],
        'root_cause': 'Display mode not persisted after reconnect',
        'resolution_steps': 'Tested with a known-good cable and port, then replaced the failing cable.',
        'resolution_summary': 'Tested with a known-good cable and port',
        'priority': 'medium',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10806',
        'title': 'Display resolution is wrong after docking',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Display resolution is wrong after docking'],
        'root_cause': 'Power delivery instability through the dock',
        'resolution_steps': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized.',
        'resolution_summary': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized',
        'priority': 'low',
        'environment': 'Docking Station',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10807',
        'title': 'Monitor flickers intermittently',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Monitor flickers intermittently'],
        'root_cause': 'Display cable path seated incorrectly',
        'resolution_steps': 'Tested with a known-good cable and port, then replaced the failing cable.',
        'resolution_summary': 'Tested with a known-good cable and port',
        'priority': 'low',
        'environment': 'Windows 11',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10808',
        'title': 'Monitor flickers intermittently',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Monitor flickers intermittently'],
        'root_cause': 'Dock firmware outdated',
        'resolution_steps': 'Re-seated the video cable, selected the correct input, and validated stable picture output.',
        'resolution_summary': 'Re-seated the video cable',
        'priority': 'low',
        'environment': 'Docking Station',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10809',
        'title': 'External screen stays black after wake',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['External screen stays black after wake'],
        'root_cause': 'USB-C dock negotiation failure',
        'resolution_steps': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized.',
        'resolution_summary': 'Rolled forward the graphics driver and confirmed resolution and refresh settings normalized',
        'priority': 'medium',
        'environment': 'Docking Station',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10810',
        'title': 'Second monitor is not detected',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['Second monitor is not detected'],
        'root_cause': 'Dock firmware outdated',
        'resolution_steps': 'Tested with a known-good cable and port, then replaced the failing cable.',
        'resolution_summary': 'Tested with a known-good cable and port',
        'priority': 'medium',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
    {
        'ticket_id': 'KB-10811',
        'title': 'External screen stays black after wake',
        'category': 'endpoint',
        'subcategory': 'display',
        'possible_system': 'Peripheral / Display',
        'keywords': ['monitor', 'display', 'dock', 'docking', 'screen', 'hdmi'],
        'symptoms': ['External screen stays black after wake'],
        'root_cause': 'Graphics driver issue after update',
        'resolution_steps': 'Power-cycled the dock and reinitialized USB-C negotiation; external display returned.',
        'resolution_summary': 'Power-cycled the dock and reinitialized USB-C negotiation; external display returned',
        'priority': 'low',
        'environment': 'Office',
        'confidence_hint': 'medium',
    },
]

RESOLUTION_TEXT_COLUMNS = [
    "resolution_summary",
    "resolution_steps",
    "solution",
    "resolved_by_it",
    "root_cause",
]
SUPPORTED_HISTORY_DATE_COLUMNS = [
    "closed_at",
    "resolved_at",
    "updated_at",
    "created_at",
    "opened_at",
]
_STOPWORDS = {
    "after",
    "again",
    "been",
    "below",
    "from",
    "have",
    "into",
    "over",
    "that",
    "then",
    "they",
    "this",
    "ticket",
    "tickets",
    "user",
    "with",
}


def normalize_text(text: str) -> str:
    text = str(text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s/.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_keywords(text: str) -> set[str]:
    normalized = normalize_text(text)
    return {
        token
        for token in normalized.split()
        if len(token) > 2 and token not in _STOPWORDS and not token.isdigit()
    }


def _safe_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _parse_date(value: Any):
    if value is None or value == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=False)
    if pd.isna(parsed):
        return None
    if getattr(parsed, "tzinfo", None) is not None:
        parsed = parsed.tz_localize(None)
    return parsed


def _best_available_history_date(record: dict[str, Any]):
    for column in SUPPORTED_HISTORY_DATE_COLUMNS:
        parsed = _parse_date(record.get(column))
        if parsed is not None:
            return parsed, column
    parsed = _parse_date(record.get("history_date"))
    if parsed is not None:
        return parsed, str(record.get("history_date_source", "history_date"))
    return None, None


def _history_date_sort_value(record: dict[str, Any]) -> pd.Timestamp:
    parsed, _ = _best_available_history_date(record)
    return parsed if parsed is not None else pd.Timestamp.min


def _resolution_signature(record: dict[str, Any]) -> str:
    return normalize_text(
        " ".join(
            [
                _safe_text(record.get("resolution_summary")),
                _safe_text(record.get("resolution_steps")),
                _safe_text(record.get("solution")),
                _safe_text(record.get("resolved_by_it")),
                _safe_text(record.get("root_cause")),
            ]
        )
    )


def _build_kb_tokens(record: dict[str, Any]) -> set[str]:
    token_sources = [
        " ".join(record.get("keywords", [])),
        " ".join(record.get("symptoms", [])),
        _safe_text(record.get("title")),
        _safe_text(record.get("resolution_summary")),
        _safe_text(record.get("resolution_steps")),
        _safe_text(record.get("root_cause")),
    ]
    return extract_keywords(" ".join(token_sources))


def _recency_bonus(record: dict[str, Any], newest_date=None) -> tuple[int, str | None]:
    record_date, date_source = _best_available_history_date(record)
    if record_date is None:
        return 0, None

    if newest_date is None:
        newest_date = record_date

    age_days = max((newest_date - record_date).days, 0)
    normalized_bonus = max(0.0, 1.0 - min(age_days, 365 * 3) / float(365 * 3))
    bonus = int(round(normalized_bonus * 15))

    if bonus <= 0:
        return 0, None

    if age_days <= 30:
        note = f"recency boost from {date_source} ({record_date.date().isoformat()}, very recent)"
    elif age_days <= 180:
        note = f"recency boost from {date_source} ({record_date.date().isoformat()}, recent)"
    else:
        note = f"recency boost from {date_source} ({record_date.date().isoformat()})"
    return bonus, note


def _normalize_record(record: dict[str, Any], source: str) -> dict[str, Any]:
    normalized = dict(record)
    history_date, history_date_source = _best_available_history_date(record)
    normalized["history_date"] = history_date
    normalized["history_date_source"] = history_date_source
    normalized["source"] = source
    normalized["resolution_signature"] = _resolution_signature(record)
    normalized["keywords"] = sorted(set(record.get("keywords", [])) | _build_kb_tokens(record))
    return normalized


def _build_embedded_history_records() -> list[dict[str, Any]]:
    grouped_ticket_ids: dict[str, list[int]] = defaultdict(list)
    for record in HISTORICAL_TICKET_KB:
        grouped_ticket_ids[normalize_text(record.get("possible_system", ""))].append(
            int(str(record.get("ticket_id", "0")).replace("KB-", "") or 0)
        )

    base_date = pd.Timestamp("2023-01-01")
    annotated_records: list[dict[str, Any]] = []

    for record in HISTORICAL_TICKET_KB:
        ticket_numeric = int(str(record.get("ticket_id", "0")).replace("KB-", "") or 0)
        system_key = normalize_text(record.get("possible_system", ""))
        system_min = min(grouped_ticket_ids.get(system_key, [ticket_numeric]))
        days_from_start = max(ticket_numeric - system_min, 0)
        history_date = base_date + timedelta(days=days_from_start * 5)
        annotated = dict(record)
        annotated["resolved_at"] = history_date.strftime("%Y-%m-%d")
        annotated_records.append(_normalize_record(annotated, "embedded_kb"))

    return annotated_records


EMBEDDED_HISTORY_RECORDS = _build_embedded_history_records()


def score_resolution_match(
    query_title: str,
    query_description: str,
    query_possible_system: str,
    kb_record: dict[str, Any],
    query_category: str | None = None,
    newest_reference_date=None,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    query_text = f"{query_title} {query_description}"
    query_tokens = extract_keywords(query_text)
    kb_tokens = _build_kb_tokens(kb_record)

    query_possible_system_norm = normalize_text(query_possible_system)
    kb_possible_system = normalize_text(kb_record.get("possible_system", ""))
    if query_possible_system_norm and query_possible_system_norm == kb_possible_system:
        score += 34
        reasons.append("same possible_system")

    query_category_norm = normalize_text(query_category or "")
    kb_category = normalize_text(kb_record.get("category", ""))
    if query_category_norm and query_category_norm == kb_category:
        score += 12
        reasons.append("same category")

    overlap = sorted(query_tokens & kb_tokens)
    if overlap:
        score += min(len(overlap) * 6, 30)
        reasons.append("keyword overlap: " + ", ".join(overlap[:5]))

    query_description_norm = normalize_text(query_description)
    symptom_overlap_tokens: set[str] = set()
    for symptom in kb_record.get("symptoms", []):
        symptom_norm = normalize_text(symptom)
        if symptom_norm and symptom_norm in query_description_norm:
            score += 16
            reasons.append("symptom phrase match")
            break
        symptom_overlap_tokens |= extract_keywords(symptom)

    symptom_keyword_overlap = sorted(query_tokens & symptom_overlap_tokens)
    if symptom_keyword_overlap:
        score += min(len(symptom_keyword_overlap) * 3, 12)
        reasons.append("symptom overlap")

    root_cause_overlap = sorted(query_tokens & extract_keywords(_safe_text(kb_record.get("root_cause"))))
    if root_cause_overlap:
        score += min(len(root_cause_overlap) * 2, 8)
        reasons.append("root cause alignment")

    dimensions_hit = sum(
        [
            bool(query_possible_system_norm and query_possible_system_norm == kb_possible_system),
            bool(query_category_norm and query_category_norm == kb_category),
            bool(overlap),
            bool(symptom_keyword_overlap),
        ]
    )
    if dimensions_hit >= 3:
        score += 8
        reasons.append("multi-dimensional match")

    recency_bonus, recency_reason = _recency_bonus(kb_record, newest_date=newest_reference_date)
    if recency_bonus:
        score += recency_bonus
        if recency_reason:
            reasons.append(recency_reason)

    return score, reasons


def _rank_candidates(
    candidates: list[dict[str, Any]],
    title: str,
    description: str,
    possible_system: str,
    category: str | None = None,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    newest_reference_date = max(
        (_history_date_sort_value(record) for record in candidates),
        default=pd.Timestamp.min,
    )
    if newest_reference_date == pd.Timestamp.min:
        newest_reference_date = None

    ranked: list[dict[str, Any]] = []
    for record in candidates:
        match_score, match_reasons = score_resolution_match(
            query_title=title,
            query_description=description,
            query_possible_system=possible_system,
            kb_record=record,
            query_category=category,
            newest_reference_date=newest_reference_date,
        )
        if match_score <= 0:
            continue

        history_date, history_date_source = _best_available_history_date(record)
        ranked.append(
            {
                "ticket_id": record.get("ticket_id", "historical-ticket"),
                "title": record.get("title", "Historical ticket"),
                "possible_system": record.get("possible_system", "Unknown"),
                "category": record.get("category", ""),
                "resolution_summary": _safe_text(record.get("resolution_summary")),
                "resolution_steps": _safe_text(record.get("resolution_steps")),
                "root_cause": _safe_text(record.get("root_cause")),
                "match_score": match_score,
                "match_reasons": match_reasons,
                "source": record.get("source", "embedded_kb"),
                "history_date": history_date,
                "history_date_source": history_date_source,
                "recency_note": next(
                    (reason for reason in match_reasons if reason.startswith("recency boost")),
                    None,
                ),
            }
        )

    ranked.sort(
        key=lambda item: (
            item["match_score"],
            item["history_date"] if item["history_date"] is not None else pd.Timestamp.min,
            item["ticket_id"],
        ),
        reverse=True,
    )
    return ranked[:top_n]


def find_relevant_resolutions(
    title: str,
    description: str,
    possible_system: str,
    category: str | None = None,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    return _rank_candidates(
        candidates=EMBEDDED_HISTORY_RECORDS,
        title=title,
        description=description,
        possible_system=possible_system,
        category=category,
        top_n=top_n,
    )


def extract_closed_ticket_history(uploaded_df) -> list[dict[str, Any]]:
    if uploaded_df is None or getattr(uploaded_df, "empty", True):
        return []

    dynamic_records: list[dict[str, Any]] = []
    available_resolution_columns = [
        column for column in RESOLUTION_TEXT_COLUMNS if column in uploaded_df.columns
    ]

    for index, row in uploaded_df.iterrows():
        status = normalize_text(row.get("status", ""))
        if status not in {"closed", "resolved", "done"}:
            continue

        resolution_parts = [_safe_text(row.get(column)) for column in available_resolution_columns]
        if not any(resolution_parts):
            continue

        title = _safe_text(row.get("title")) or _safe_text(row.get("short_description")) or "historical ticket"
        symptom_text = _safe_text(row.get("short_description")) or title
        summary = (
            _safe_text(row.get("resolution_summary"))
            or _safe_text(row.get("solution"))
            or _safe_text(row.get("resolved_by_it"))
            or _safe_text(row.get("root_cause"))
        )
        steps = (
            _safe_text(row.get("resolution_steps"))
            or _safe_text(row.get("resolved_by_it"))
            or _safe_text(row.get("solution"))
        )

        record = {
            "ticket_id": _safe_text(row.get("ticket_id")) or f"uploaded-history-{index}",
            "title": title,
            "category": _safe_text(row.get("category")),
            "subcategory": _safe_text(row.get("subcategory")),
            "possible_system": _safe_text(row.get("possible_system")) or "Unknown",
            "keywords": sorted(
                extract_keywords(
                    " ".join(
                        [
                            title,
                            symptom_text,
                            _safe_text(row.get("category")),
                            _safe_text(row.get("subcategory")),
                            _safe_text(row.get("environment")),
                        ]
                    )
                )
            ),
            "symptoms": [symptom_text],
            "root_cause": _safe_text(row.get("root_cause")),
            "resolution_steps": steps,
            "resolution_summary": summary,
            "solution": _safe_text(row.get("solution")),
            "resolved_by_it": _safe_text(row.get("resolved_by_it")),
            "priority": _safe_text(row.get("priority")),
            "environment": _safe_text(row.get("environment")),
            "confidence_hint": "high",
        }

        for date_column in SUPPORTED_HISTORY_DATE_COLUMNS:
            if date_column in uploaded_df.columns:
                record[date_column] = row.get(date_column)

        dynamic_records.append(_normalize_record(record, "uploaded_history"))

    return dynamic_records


def find_relevant_resolutions_with_uploaded_history(
    title: str,
    description: str,
    possible_system: str,
    category: str | None = None,
    uploaded_df=None,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    candidates = EMBEDDED_HISTORY_RECORDS + extract_closed_ticket_history(uploaded_df)
    return _rank_candidates(
        candidates=candidates,
        title=title,
        description=description,
        possible_system=possible_system,
        category=category,
        top_n=top_n,
    )


def detect_resolution_evolution(
    possible_system: str,
    category: str | None = None,
    uploaded_df=None,
    min_records: int = 4,
) -> list[str]:
    candidates = EMBEDDED_HISTORY_RECORDS + extract_closed_ticket_history(uploaded_df)
    filtered = [
        record
        for record in candidates
        if normalize_text(record.get("possible_system", "")) == normalize_text(possible_system)
    ]
    if category:
        filtered = [
            record
            for record in filtered
            if normalize_text(record.get("category", "")) == normalize_text(category)
        ]

    filtered = [record for record in filtered if record.get("resolution_signature")]
    filtered.sort(key=_history_date_sort_value)

    if len(filtered) < min_records:
        return []

    midpoint = len(filtered) // 2
    older_records = filtered[:midpoint]
    newer_records = filtered[midpoint:]
    if not older_records or not newer_records:
        return []

    older_signatures = {record["resolution_signature"] for record in older_records}
    newer_signatures = {record["resolution_signature"] for record in newer_records}
    overlap_ratio = len(older_signatures & newer_signatures) / max(
        1, len(older_signatures | newer_signatures)
    )
    if overlap_ratio >= 0.6:
        return []

    older_tokens = Counter()
    newer_tokens = Counter()
    for record in older_records:
        older_tokens.update(extract_keywords(record.get("resolution_signature", "")))
    for record in newer_records:
        newer_tokens.update(extract_keywords(record.get("resolution_signature", "")))

    older_terms = [token for token, _ in older_tokens.most_common(4)]
    newer_terms = [token for token, _ in newer_tokens.most_common(4)]
    distinctive_old = [term for term in older_terms if term not in set(newer_terms)]
    distinctive_new = [term for term in newer_terms if term not in set(older_terms)]

    older_date = _history_date_sort_value(older_records[-1]).date().isoformat()
    newer_date = _history_date_sort_value(newer_records[0]).date().isoformat()
    system_label = possible_system or "this issue family"

    if distinctive_old and distinctive_new:
        return [
            (
                f"For {system_label}, older tickets through {older_date} emphasized "
                f"{', '.join(distinctive_old[:2])}, while recent tickets since {newer_date} "
                f"emphasize {', '.join(distinctive_new[:2])}."
            )
        ]

    return [
        f"For {system_label}, the preferred resolution approach appears to have changed in recent tickets."
    ]
