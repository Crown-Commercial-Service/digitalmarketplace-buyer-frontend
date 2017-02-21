Feature: Build brief
    Buyers can build briefs.

Scenario: Anonymous users cannot create brief
    Given I am an anonymous user
    And I am on the / page
    When I click the Find an individual specialist link
    And the Finding an individual specialist page loads
    And I click the Create brief button
    Then I should see the Sign in to the Marketplace page

Scenario: Suppliers cannot create brief
    Given I am a Supplier
    And I am on the / page
    When I click the Find an individual specialist link
    And the Finding an individual specialist page loads
    And I click the Create brief button
    Then I should see the Sign in to the Marketplace page

Scenario: Buyers can create a brief
    Given I am a Buyer
    And I am on the / page
    When I click the Find an individual specialist link
    And the Research, write and publish your brief page loads
    And I click the Create brief button
    And the Create a title for your brief page loads
    And I enter a title
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Select a digital specialist for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Specialist role link
    And the Ethical Hacker page loads
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Select a location for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Location link
    And the New South Wales page loads
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Enter the Description of work for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Description of work link
    And the Who will the specialist work for? page loads
    And I click the Add organisation link
    And I enter My Org into organisation on the Please write in full, including the state if necessary page
    And I enter Task to complete into specialistWork on the List all tasks you want the specialist to do page
    And I enter People you will work with into existingTeam on the Describe the team the specialist will be working with page
    And I enter Additional Info into additionalRelevantInformation on the Provide any additional relevant information page
    And I enter Surry Hills NSW into workplaceAddress on the If you don't have the full address page
    And I enter These are the working arrangements into workingArrangements on the Describe how you want to work with the individual page
    And I enter I have security clearance into securityClearance on the Only request security clearance page
    And I enter 01/01/2016 into startDate on the What is the latest start date page
    And I enter 6 months into contractLength on the Contracts cannot exceed 12 months page
    And I enter This is an additional term into additionalTerms on the If you need to set out any additional terms and conditions page
    And I enter $100 per day into budgetRange on the Enter a maximum day rate page
    And I enter Summary of the brief into summary on the This will be the first thing sellers see page
    Then I should see the Description of work page

Scenario: Enter the Evaluation process for your brief
    Given I am a Buyer
    And I have created a brief
    When I click the Shortlist and evaluation process link
    And the There are 3 stages to finding the specialist page loads
    And I click the Set maximum number of specialists you’ll evaluate link
    And I enter 3 into numberOfSuppliers on the We recommend you evaluate at least 3 page
    And I enter 30,20,50 into technicalWeighting,culturalWeighting,priceWeighting on the Use the weightings to say how important page
    And I enter This is an essential requirement into essentialRequirements on the When evaluating always consider page
    And I enter A cultural fit requirement into culturalFitCriteria on the Cultural fit is how well you page
    And the How will you verify the specialist is right for the role? page loads
    And I click the Save and continue button
    Then I should see the There are 3 stages to finding the specialist page

Scenario: Select how long your brief will be open
    Given I am a Buyer
    And I have created a brief
    When I click the How long your brief will be open link
    And the 1 week page loads
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Select who can respond
    Given I am a Buyer
    And I have created a brief
    When I click the Who can respond link
    And the All qualified sellers page loads
    And I select an option in the list
    And I click the Save and continue button
    Then I should see the Overview

Scenario: Review and publish your requirements
    Given I am a Buyer
    And I have created a brief
    When I click the Review and publish your requirements link
    Then I should see the All requirements are published on the Digital Marketplace page
