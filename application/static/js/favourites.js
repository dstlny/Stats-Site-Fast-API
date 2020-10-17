$(document).ready(() => {
	$('.favourite').hide();

	(function(favourites, $, undefined ) {

		if (typeof(localStorage) !== "undefined") {

			// private vars
			let $fav_player = $('#favourite_player > i')
			const current_modules = ['pubg', 'cod']

			// public vars and functions
			favourites.fav_available = true

			favourites.getFavourites = () => {
				let these = window.localStorageService.getFromLocalStorage('favourites')
				if(these === null){
					window.localStorageService.setInLocalStorage('favourites', {pubg:[], cod:[]})
					these = window.localStorageService.getFromLocalStorage('favourites')
				}
				return these
			}
			
			favourites.initFavourites = (this_mod) => {
				let these = favourites.getFavourites()
				let module_favourites = these[this_mod]

				if(module_favourites && module_favourites.length > 0){		
					if(module_favourites.some(module_favourite => module_favourite.href.includes(window.location.href))){
						$fav_player.attr('class', 'fas fa-star');
					}
				}
			}

			favourites.removeFromFavourites = (this_mod, id, search_href) => {
				let these = favourites.getFavourites()
				let module_favourites = these[this_mod]
				for (let i =0; i < module_favourites.length; i++){
					if (module_favourites[i].href.includes(search_href)){
						if(module_favourites[i].href.includes(window.location.href)) $fav_player.attr('class', 'far fa-star');
						module_favourites.splice(i, 1);
						break;
					}
				}
				window.localStorageService.setInLocalStorage('favourites', these)
				favourites.handleFavourites(id)
			}

			favourites.handleFavourites = (id) => {
				if(window.authService.authed){
					let these = favourites.getFavourites()
	
					$(id).empty();
					let html = [];
					let iter = 0;
					let module_favourites;
					for(const current_module of current_modules){
						if(these[current_module] && these[current_module].length > 0){
							module_favourites = these[current_module]
							html.push(`
								${iter == 0 ? '' : '<hr>'}
								<h4>${current_module.toUpperCase()} Favourites</h4>
								<ol>
							`)
							for (let i =0; i < module_favourites.length; i++){
								html.push(`
									<li>
										<a href='${module_favourites[i].href}'>
											${module_favourites[i].text}
										</a>
										<i type="button" class="fas fa-star" onclick='window.favouritesService.removeFromFavourites("${current_module}", "${id}", "${module_favourites[i].href}")'></i>
									</li>
								`)
							}
							html.push(`</ol>`)
							iter += 1
						}	
					}
					if(html.length === 0){
						html.push('Sorry, currently no favourites')
					}
					$(id).html(html.join('')).show()
				}
			}

			favourites.pushFavouriteForModule = (this_mod, favourite) => {
				if(window.authService.authed){
					let these = favourites.getFavourites()
					let module_favourites = these[this_mod]
	
					// in favourites
					if($fav_player.hasClass('fas fa-star')){
						for (let i =0; i < module_favourites.length; i++){
							if (module_favourites[i].href.includes(window.location.href)){
								module_favourites.splice(i, 1);
								break;
							}
						}
						window.localStorageService.setInLocalStorage('favourites', these)
						$fav_player.attr('class', 'far fa-star');
					} else { // not in favourites
						if(!(module_favourites.some(module_favourite => module_favourite.href == favourite.href))){
							module_favourites.push(favourite)
							window.localStorageService.setInLocalStorage('favourites', these)
						}
						$fav_player.attr('class', 'fas fa-star');
					}
				}
			}

		} else {
			favourites.fav_available = false
			alert('"Favourites" functionality will be disabled')
		}

	}(window.favouritesService = window.favouritesService || {}, jQuery));

});