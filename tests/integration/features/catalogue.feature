Feature: Supplier Catalogue
    Buyers can search and view Suppliers.

Scenario: Navigate to search page
    Given I am on the / page
    When I click the View approved sellers link
    Then I should see the Seller search – Digital Marketplace page

Scenario: Anonymous users cannot view supplier details
    Given I am an anonymous user
    And I am on the /search/sellers page
    When I click the first supplier link
    Then I should see the Log in – Digital Marketplace page

Scenario: Buyers can view supplier details
    Given I am a Buyer
    And I am on the /search/sellers page
    When I click the first supplier link
    Then I should see Company Details text
