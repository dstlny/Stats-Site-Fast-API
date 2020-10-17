$(document).ready(() => {

	(function(recent_searches, $, undefined ) {

		// public vars and functions

		recent_searches.getRecentSearchesForModule = (sys_module, should_return) => {
			let searches = window.localStorageService.getFromLocalStorage('recentSearches');
	
			if(searches && searches.length > 0){
				if(sys_module){
					searches = searches.filter(
						player =>  typeof player.module !== undefined && player.module == sys_module
					).map(player =>  `<a href="${player.href}">${player.text}</a> <i class="fa fa-times" onclick="window.recentSearchesService.removeFromRecentSearches('${sys_module}', '${player.href}');")></i>`);
				}
			} else {
				window.localStorageService.setInLocalStorage('recentSearches', []);
				these = []
			}
	
			if(should_return){
				return searches
			} else {
				recent_searches.formatRecentSearches(searches)
			}
		}

		recent_searches.formatRecentSearches = (searches) => {
			if(searches && searches.length > 0){
				$('#recent_searches').html('<hr><h6>Some of your recent Searches:</h6>' + searches.join(' | '));
				$('#recent_searches').show();
				$('#recent_searches').children().show();
			} else {
				$('#recent_searches').hide();
				$('#recent_searches').children().hide();
			}
		}

		recent_searches.pushNewRecentSearchToRecentSearches = (new_search) => {
			let searches = recent_searches.getRecentSearchesForModule(null, true)
	
			if(!(searches.some(recent => recent.text === new_search.text))) {
				searches.push(new_search)
				window.localStorageService.setInLocalStorage('recentSearches', searches);
			}
	
		}

		recent_searches.removeFromRecentSearches = (sys_module, search_href) => {
			let searches = window.localStorageService.getFromLocalStorage('recentSearches');
	
			searches = searches.filter(
				player =>  typeof player.module !== undefined && player.module == sys_module
			)
	
			if(searches && searches.length > 0){
				for (let i =0; i < searches.length; i++){
					if (searches[i].href.includes(search_href)){
						searches.splice(i, 1);
						break;
					}
				}
				window.localStorageService.setInLocalStorage('recentSearches', searches);
				recent_searches.getRecentSearchesForModule(sys_module, false)
			}
		}
	}(window.recentSearchesService = window.recentSearchesService || {}, jQuery));

});