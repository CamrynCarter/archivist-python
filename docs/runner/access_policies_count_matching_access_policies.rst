.. _access_policies_count_matching_access_policiesyamlref:

Access Policies Count Matching AccessPolicies Story Runner YAML
...............................................................

Count all access policies that match an asset.

The :code:`print_response` setting should be specified as :code:`True` in order to see the results.

.. code-block:: yaml
    
    ---
    steps:
      - step:
          action: ACCESS_POLICIES_COUNT_MATCHING_ACCESS_POLICIES
          description: Count all access policies that match an asset
          print_response: true
          asset_label: an asset
