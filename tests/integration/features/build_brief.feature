Feature: Build brief
    Buyers can build briefs.

Scenario: Anonymous users cannot create brief
    Given I am an anonymous user
    And I am on the / page
    When I click the Find an individual specialist link
    And I click the Create brief button
    Then I should see the Log in – Digital Marketplace page

Scenario: Suppliers cannot create brief
    Given I am a Supplier
    And I am on the / page
    When I click the Find an individual specialist link
    And I click the Create brief button
    Then I should see the Log in – Digital Marketplace page

Scenario: Buyers can create a brief
    Given I am a Buyer
    And I am on the / page
    When I click the Find an individual specialist link
    And I click the Create brief button
    And I enter a title
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Select a digital specialist for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Specialist role link
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Select a location for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Location link
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Enter the Description of work for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Description of work link
    And I click the Add organisation link
    And I enter My Org into organisation
    And I enter Task to complete into specialistWork
    And I enter People you will work with into existingTeam
    And I enter Additional Info into additionalRelevantInformation
    And I enter Surry Hills NSW into workplaceAddress
    And I enter These are the working arrangements into workingArrangements
    And I enter I have security clearnace into securityClearance
    And I enter 01/01/2016 into startDate
    And I enter 6 months into contractLength
    And I enter This is an additional term into additionalTerms
    And I enter $100 per day into budgetRange
    And I enter Summary of the brief into summary
    Then I should see the Description of work – Digital Marketplace page

Scenario: Enter the Evaluation process for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Shortlist and evaluation process link
    And I click the Set maximum number of specialists you’ll evaluate link
    And I enter 3 into numberOfSuppliers
    And I enter 30,20,50 into technicalWeighting,culturalWeighting,priceWeighting
    And I enter This is an essential requirement into essentialRequirements
    And I enter A cultural fit requirement into culturalFitCriteria
    And I click the Save and continue button
    Then I should see the Shortlist and evaluation process – Digital Marketplace page

Scenario: Select how long your brief will be open
    Given I am a Buyer
    And I have created a brief
    When I click the How long your brief will be open link
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Select who can respond
    Given I am a Buyer
    And I have created a brief
    When I click the Who can respond link
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Review and publish your requirements
    Given I am a Buyer
    And I have created a brief
    When I click the Review and publish your requirements link
    Then I should see the Your account - Digital Marketplace page

