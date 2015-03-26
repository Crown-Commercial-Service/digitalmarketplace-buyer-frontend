def _service_availability(service):
    result = {}
    if 'serviceAvailabilityPercentage' in service:
        return {
            'value': (
                str(service['serviceAvailabilityPercentage']['value']) + '%'
            ),
            'assurance': service['serviceAvailabilityPercentage']['assurance']
        }
    else:
        return False

mappings = [
    {
        'name': u'Support',
        'rows': [
            {
                'key': u'Support service type',
                'value': 'supportTypes'
            },
            {
                'key': u'Support accessible to any third-party suppliers',
                'value': 'supportForThirdParties'
            },
            {
                'key': u'Support availablility',
                'value': 'supportAvailability'
            },
            {
                'key': u'Standard support response times',
                'value': 'supportResponseTime'
            },
            {
                'key': u'Incident escalation process available',
                'value': 'incidentEscalation'
            },
        ]
    },
    {
        'name': u'Open standards',
        'rows': [
            {
                'key': u'Open standards supported and documented',
                'value': 'openStandardsSupported'
            },
        ]
    },
    {
        'name': u'Onboarding and offboarding',
        'rows': [
            {
                'key': u'Service onboarding process included',
                'value': 'serviceOnboarding'
            },
            {
                'key': u'Service offboarding process included',
                'value': 'serviceOffboarding'
            },
        ]
    },
    {
        'name': u'Analytics',
        'rows': [
            {
                'key': u'Real-time management information available',
                'value': 'analyticsAvailable'
            }
        ]
    },
    {
        'name': u'Cloud features',
        'rows': [
            {
                'key': u'Elastic cloud approach supported',
                'value': 'elasticCloud'
            },
            {
                'key': u'Guaranteed resources defined',
                'value': 'guaranteedResources'
            },
            {
                'key': u'Persistent storage supported',
                'value': 'persistentStorage'
            }
        ]
    },
    {
        'name': u'Provisioning',
        'rows': [
            {
                'key': u'Self-service provisioning supported',
                'value': 'selfServiceProvisioning'
            },
            {
                'key': u'Service provisioning time',
                'value': 'provisioningTime'
            },
            {
                'key': u'Service deprovisioning time',
                'value': 'deprovisioningTime'
            }
        ]
    },
    {
        'name': u'Open source',
        'rows': [
            {
                'key': u'Open-source software used and supported',
                'value': 'openSource'
            }
        ]
    },
    {
        'name': u'Code libraries',
        'rows': [
            {
                'key': u'Languages code libraries are written in',
                'value': 'codeLibraryLanguages'
            }
        ]
    },
    {
        'name': u'API access',
        'rows': [
            {
                'key': u'API access available and supported',
                'value': 'apiAccess'
            },
            {
                'key': u'API type',
                'value': 'apiType'
            }
        ]
    },
    {
        'name': u'Networks and connectivity',
        'rows': [
            {
                'key': u'Networks the service is directly connected to',
                'value': 'networksConnected'
            }
        ]
    },
    {
        'name': u'Access',
        'rows': [
            {
                'key': u'Supported web browsers',
                'value': 'supportedBrowsers'
            },
            {
                'key': u'Offline working and syncing supported',
                'value': 'offlineWorking'
            },
            {
                'key': u'Supported devices',
                'value': 'supportedDevices'
            }
        ]
    },
    {
        'name': u'Certifications',
        'rows': [
            {
                'key': u'Vendor certification(s)',
                'value': 'vendorCertifications'
            }
        ]
    },
    {
        'name': u'Identity standards',
        'rows': [
            {
                'key': u'Identity standards used by the service',
                'value': 'identityStandards'
            }
        ]
    },
    {
        'name': u'Data storage',
        'rows': [
            {
                'key': (
                    u'Datacentres adhere to EU Code of Conduct for Operations'
                ),
                'value': 'datacentresEUCode'
            },
            {
                'key': u'User-defined data location',
                'value': 'datacentresSpecifyLocation'
            },
            {
                'key': u'Datacentre tier',
                'value': 'datacentreTier'
            },
            {
                'key': (
                    u'Backup, disaster recovery and resilience plan in place'
                ),
                'value': 'dataBackupRecovery'
            },
            {
                'key': u'Data extraction/removal plan in place',
                'value': 'dataExtractionRemoval'
            }
        ]
    },
    {
        'name': u'Data-in-transit protection',
        'rows': [
            {
                'key': u'Data protection between user device and service',
                'value': 'dataProtectionBetweenUserAndService'
            },
            {
                'key': u'Data protection within service',
                'value': 'dataProtectionWithinService'
            },
            {
                'key': u'Data protection between services',
                'value': 'dataProtectionBetweenServices'
            }
        ]
    },
    {
        'name': u'Asset protection and resilience',
        'rows': [
            {
                'key': u'Datacentre location',
                'value': 'datacentreLocations'
            },
            {
                'key': u'Data management location',
                'value': 'dataManagementLocations'
            },
            {
                'key': u'Legal jurisdiction of service provider',
                'value': 'legalJurisdiction'
            },
            {
                'key': u'Datacentre protection',
                'value': 'datacentreProtectionDisclosure'
            },
            {
                'key': u'Data-at-rest protection',
                'value': 'dataAtRestProtections'
            },
            {
                'key': u'Secure data deletion',
                'value': 'dataSecureDeletion'
            },
            {
                'key': u'Storage media disposal',
                'value': 'dataStorageMediaDisposal'
            },
            {
                'key': u'Secure equipment disposal',
                'value': 'dataSecureEquipmentDisposal'
            },
            {
                'key': u'Redundant equipment accounts revoked',
                'value': 'dataRedundantEquipmentAccountsRevoked'
            },
            {
                'key': u'Service availability',
                'value': _service_availability
            }
        ]
    },
    {
        'name': u'Separation between consumers',
        'rows': [
            {
                'key': u'Cloud deployment model',
                'value': 'cloudDeploymentModel'
            },
            {
                'key': u'Type of consumer',
                'value': 'otherConsumers'
            },
            {
                'key': u'Services separation',
                'value': 'servicesSeparation'
            },
            {
                'key': u'Services management separation',
                'value': 'servicesManagementSeparation'
            }
        ]
    },
    {
        'name': u'Governance',
        'rows': [
            {
                'key': u'Governance framework',
                'value': 'governanceFramework'
            }
        ]
    },
    {
        'name': u'Configuration and change management',
        'rows': [
            {
                'key': u'Configuration and change management tracking',
                'value': 'configurationTracking'
            },
            {
                'key': u'Change impact assessment',
                'value': 'changeImpactAssessment'
            }
        ]
    },
    {
        'name': u'Vulnerabilility management',
        'rows': [
            {
                'key': u'Vulnerability assessment',
                'value': 'vulnerabilityAssessment'
            },
            {
                'key': u'Vulnerability monitoring',
                'value': 'vulnerabilityMonitoring'
            },
            {
                'key': u'Vulnerability mitigation prioritisation',
                'value': 'vulnerabilityMitigationPrioritisation'
            },
            {
                'key': u'Vulnerability tracking',
                'value': 'vulnerabilityTracking'
            },
            {
                'key': u'Vulnerability mitigation timescales',
                'value': 'vulnerabilityTimescales'
            }
        ]
    },
    {
        'name': u'Event monitoring',
        'rows': [
            {
                'key': u'Event monitoring',
                'value': 'eventMonitoring'
            }
        ]
    },
    {
        'name': u'Incident management',
        'rows': [
            {
                'key': u'Incident management processes',
                'value': 'incidentManagementProcess'
            },
            {
                'key': u'Consumer reporting of security incidents',
                'value': 'incidentManagementReporting'
            },
            {
                'key': u'Security incident definition published',
                'value': 'incidentDefinitionPublished'
            }
        ]
    },
    {
        'name': u'Personnel security',
        'rows': [
            {
                'key': u'Personnel security checks',
                'value': 'personnelSecurityChecks'
            }
        ]
    },
    {
        'name': u'Secure development',
        'rows': [
            {
                'key': u'Secure development',
                'value': 'secureDevelopment'
            },
            {
                'key': u'Secure design, coding, testing and deployment',
                'value': 'secureDesign'
            },
            {
                'key': u'Software configuration management',
                'value': 'secureConfigurationManagement'
            }
        ]
    },
    {
        'name': u'Supply-chain security',
        'rows': [
            {
                'key': u'Visibility of data shared with third-party suppliers',
                'value': 'thirdPartyDataSharingInformation'
            },
            {
                'key': u'Third-party supplier security requirements',
                'value': 'thirdPartySecurityRequirements'
            },
            {
                'key': u'Third-party supplier risk assessment',
                'value': 'thirdPartyRiskAssessment'
            },
            {
                'key': u'Third-party supplier compliance monitoring',
                'value': 'thirdPartyComplianceMonitoring'
            },
            {
                'key': u'Hardware and software verification',
                'value': 'hardwareSoftwareVerification'
            }
        ]
    },
    {
        'name': u'Authentication of consumers',
        'rows': [
            {
                'key': u'User authentication and access management',
                'value': 'userAuthenticateManagement'
            },
            {
                'key': u'User access control through support channels',
                'value': 'userAuthenticateSupport'
            }
        ]
    },
    {
        'name': u'Separation and access control within management interfaces',
        'rows': [
            {
                'key': u'User access control within management interfaces',
                'value': 'userAccessControlManagement'
            },
            {
                'key': u'Administrator permissions',
                'value': 'restrictAdministratorPermissions'
            },
            {
                'key': u'Management interface protection',
                'value': 'managementInterfaceProtection'
            }
        ]
    },
    {
        'name': u'Identity and authentication',
        'rows': [
            {
                'key': u'Identity and authentication controls',
                'value': 'identityAuthenticationControls'
            }
        ]
    },
    {
        'name': u'External interface protection',
        'rows': [
            {
                'key': u'Onboarding guidance provided',
                'value': 'onboardingGuidance'
            },
            {
                'key': u'Interconnection method provided',
                'value': 'interconnectionMethods'
            }
        ]
    },
    {
        'name': u'Secure service administration',
        'rows': [
            {
                'key': u'Service management model',
                'value': 'serviceManagementModel'
            }
        ]
    },
    {
        'name': u'Audit information provision to consumers',
        'rows': [
            {
                'key': u'Audit information provided',
                'value': 'auditInformationProvided'
            }
        ]
    },
    {
        'name': u'Secure use of the service by the customer',
        'rows': [
            {
                'key': u'Device access method',
                'value': 'deviceAccessMethod'
            },
            {
                'key': u'Service configuration guidance',
                'value': 'serviceConfigurationGuidance'
            },
            {
                'key': u'Training',
                'value': 'trainingProvided'
            }
        ]
    }
]
