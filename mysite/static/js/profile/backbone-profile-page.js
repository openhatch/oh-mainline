Profile = new Backbone.Marionette.Application();

Profile.addRegions({
    portfolio: "#portfolio-entries"
});
    
PortfolioEntry = new Backbone.Model.extend({
    defaults: {
        project__name: 'Twisted',
        project__icon: '/404.png',
        project_url: '/+projects/twisted/',
        project_description: 'The engine of your internets',
        experience_description: 'I hacked the RSS feed reader.',
        is_published: true,
        is_deleted: false,
        is_archived: false,
        sort_order: 0,
        receive_maintainer_updates: true,
        citation_list: [{   url: 'http://sample.com', 
                            description: 'Link to the bug I fixed'
                       }]
        }
});
    
Portfolio = new Backbone.Collection.extend({
    model: PortfolioEntry,
    comparator: function(entry){
        return entry.get('sort_order');
        }
});

PortfolioEntryView = Backbone.Marionette.ItemView.extend({
    template: '#portfolio-entry-template',
    className: 'portfolio_entry'
});

PortfolioView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    id: 'portfolio-entries-list',
    template: '#portfolio-entries-list-template',
    itemView: PortfolioEntryView,
    
    appendHtml: function(collectionView, itemView) { collectionView.$('ul').append(itemView.el); }
    });
    
Profile.addInitializer(function(options){
    var portfolioView = new PortfolioView({
        collection: options.portfolio
    });
    Profile.portfolio.show(portfolioView);
    });
    
$(document).ready(function(){
    var portfolio = new Portfolio([
        new PortfolioEntry ({ 
            project__name: 'Wet Cat', 
            project_description: 'A cat that is wet.', 
            receive_maintainer_updates: false
            }),
        new PortfolioEntry ({ 
            project__name: 'Bitey', 
            project_description: 'A rather angry cat emulator.', 
            experience_description: 'I hacked your face.'
            }),
        new PortfolioEntry ({ 
            project__name: 'Ceiling Cat', 
            receive_maintainer_updates: false
            })
        ]);
    Profile.start({ portfolio: portfolio });
    
    });

