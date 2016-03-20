Feature: Boundaries
  As a DevOps,
  I want to see the boundaries of a system
  so that I know how to interact with it.

  Scenario: Exposed ports
    Given a file named "compose.yml" with:
      """
      version: "2"
      services:
        service:
          ports:
            - 8080
      """
    When I run `bin/compose_plantuml --boundaries compose.yml`
    Then it should pass with exactly:
      """
      skinparam componentStyle uml2
      rectangle system {
        [service]
      }
      [service] --> 8080

      """

  Scenario: Alias Ports
    Given a file named "compose.yml" with:
      """
      version: "2"
      services:
        service:
          ports:
            - 8080:80
      """
    When I run `bin/compose_plantuml --boundaries compose.yml`
    Then it should pass with exactly:
      """
      skinparam componentStyle uml2
      rectangle system {
        [service]
      }
      [service] --> 8080 : 80

      """
