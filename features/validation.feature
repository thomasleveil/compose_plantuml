Feature: Validation
  As a DevOps,
  I want to have error messages for invalid compose input
  so that I'm sure it works if it does not return an error.

  Scenario: Requires Version
    Given a file named "compose.yml" with:
      """
      foo:
        image: bar
      """
    When I run `bin/compose_plantuml --link-graph compose.yml`
    Then it should fail with:
      """
      docker-compose version exception: version not present
      """

  Scenario: Requires Version 2
    Given a file named "compose.yml" with:
      """
      version: 1
      """
    When I run `bin/compose_plantuml --link-graph compose.yml`
    Then it should fail with exactly:
      """
      docker-compose version exception: need version 2, but got 1

      """
