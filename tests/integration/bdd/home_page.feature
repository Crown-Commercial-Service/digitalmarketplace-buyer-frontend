Feature: Home page
    Users can view home page.

Scenario: Anonymous users can click Dashboard opportunities
    Given I am an anonymous user
    And I am on the / page
    When I click the View the latest briefs text
    Then I should see the Latest opportunities page

Scenario: Anonymous users can click Dashboard sellers
    Given I am an anonymous user
    And I am on the / page
    When I click the Browse the catalogue text
    Then I should see the Seller catalogue page

Scenario: Anonymous users can click Dashboard buyers
    Given I am an anonymous user
    And I am on the / page
    When I click the Create a buyer account text
    Then I should see the Digital Marketplace buyer account holders page

