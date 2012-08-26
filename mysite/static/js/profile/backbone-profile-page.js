Profile = new Backbone.Marionette.Application();

Profile.addRegions({
    portfolio: "#portfolio-entries.edit"
});
    
PortfolioEntry = Backbone.Model.extend({
    defaults: {
        project_id: 1,
        save_status: true
        },
    urlRoot: '/+api/v1/profile/portfolio_entry/'
});
    
Portfolio = Backbone.Collection.extend({
    model: PortfolioEntry,
    comparator: function(entry){
        return entry.get('sort_order');
        },
    urlRoot: '/+api/v1/profile/portfolio_entry/'
});

PortfolioEntryView = Backbone.Marionette.ItemView.extend({
    template: '#portfolio-entry-template',
    className: 'portfolio_entry edit',
    tagName: 'li'
});

PortfolioView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    id: 'portfolio-entries-all',
    className: 'edit',
    template: '#portfolio-entries-list-template',
    itemView: PortfolioEntryView,
    
    appendHtml: function(collectionView, itemView) { collectionView.$('#portfolio-entries-list').append(itemView.el); }
    });
    
Profile.addInitializer(function(options){
    var portfolioView = new PortfolioView({
        collection: options.portfolio
    });
    Profile.portfolio.show(portfolioView);
    });
    
$(document).ready(function(){
    var portfolio = new Portfolio([]);
    
    $.ajax({
        type: "GET", 
        url: '/+api/v1/profile/portfolio_entry/'
        })
        .done(function(data) {
            _.each(data.objects, function(entry){
                portfolio.add(new PortfolioEntry(entry));
            });
        });
    
    Profile.start({ portfolio: portfolio });
    
    });

