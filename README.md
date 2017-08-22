# GitHub Enterprise Python API

Provides an API over the Site Admin tools for GitHub Enterprise.

Requires a Site Admin username and password to login to the UI via Selenium.

We chose this design as there's no official API for retrieving the list of dormant
users, paging through the audit log, or to force resync an LDAP user. But it's
available in the UI so... /shrug

## Install

You can [install with pip from github](https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support).

    pip install git+git://github.com/peak6/github_enterprise.git@v0.1.0#egg=github_enterprise

## Usage

This simple example demonstrates the API.

    from github_enterprise import GithubEnterprise
    from datetime import datetime, timedelta
    
    gh_user = "myuser"
    gh_pwd = "mypwd"
    gh_url = "https://github.example.com"
    window = 30  # days (GHE "dormant users" assumes 30 days so our window should too)
    
    with GithubEnterprise(gh_user, gh_pwd, gh_url) as ghe:
        for username in ghe.get_dormant_users():
    
            # "Dormant" doesn't consider users who are mostly read-only
            # Let's validate the user hasn't even logged in recently before removing them
            audit_date, audit_msg = ghe.get_latest_audit_log(username)
    
            cutoff_datetime = datetime.today() - timedelta(days=window)
            if audit_date is None or audit_date < cutoff_datetime:
                print "Removing dormant user: %s" % username
    
                # ... remove the user from LDAP ...
    
                # force re-sync the removed users to make the seats available immediately
                ghe.resync_user_ldap(username)

## Compatibility

This library has been tested against GitHub Enterprise version 2.9.4.

