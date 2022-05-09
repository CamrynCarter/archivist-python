.. _access_policies_count_matching_assetsyamlref:

Access Policies Count Matching Assets Story Runner YAML
.......................................................

Count all assets that match an access_policy.

The :code:`print_response` setting should be specified as :code:`True` in order to see the results.

.. code-block:: yaml
    
    ---
    steps:
      - step:
          action: ACCESS_POLICIES_COUNT_MATCHING_ASSETS
          description: Count all assets that match an access_policy
          print_response: true
          access_policy_label: an access policy
