===========================
 Adding a new bug tracker
===========================

One of the pillars of OpenHatch is helping project owners get in touch with
developers willing to help, by offering them easy to fix bugs where they can get
started. In order to do this, OpenHatch crawls bugtrackers of many projects and
features them in the site.

If you have a project that you want to add to OpenHatch you can do it very
easily following these steps.

- Go to http://openhatch.org/customs/
- In the "Tracker Type" select box select the bug tracker that your project uses. If your bug tracker is not in that list, it may be a good a idea to contact us and let us know.
- Click on "Add a tracker" to add a new tracker
- You will be directed to a form where you need to fill specific information about your tracker. This form changes depending on the tracker type.

For Trac and Roundup:

- Fill the new tracker form like this:
    - Tracker name: Name of your project
    - Base url: This is the URL to the homepage of the Trac tracker instance. Remove any subpaths like 'ticket/' or 'query' from this.
    - Bug project name format: This field contains instructions of how to fill it, but if you are not sure, probably {tracker_name} is the best option.
    - Bitesized type: Choose the field that can help identify a bug as bite-sized. If you don't find the field you need in the select box, you may have to contact us to add it.
    - Bitesized text: The value that the Bitesized type contains for a bite-sized ticket.
    - Documentation type: Ditto Bitesized type.
    - Documentation text: Ditto Documentation text.
    - As appears in distribution: For most cases you can leave this field empty.
- Click "Next" and you will be directed to another form:
    - Url: Enter the URL of the CSV representation of a search result that only returns bitesized bugs for your project. Here is an example of how the value for that field looks for the GHC Tracker (Trac): hackage.haskell.org/trac/ghc/query?status=new&group=difficulty&format=csv&order=id&difficulty=Easy+%28less+than+1+hour%29&col=id&col=summary&col=status&col=owner&col=milestone&col=component&col=version&desc=1
    - Description: Enter a description of the results that the search query returns.
- Click "Finish".
