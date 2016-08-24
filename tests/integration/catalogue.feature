Feature: Supplier Catalogue
    Buyers can search and view Suppliers.

Scenario: Navigate to search page
    Given I am on the home page
    When I click the Browse sellers link
    Then I should see the Suppliers search – Digital Marketplace page
