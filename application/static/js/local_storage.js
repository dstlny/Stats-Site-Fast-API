(function(local_storage, $, undefined ) {

	// public vars and functions

	if (typeof(localStorage) !== "undefined") {
		local_storage.local_storage_available = true
		local_storage.setInLocalStorage = (name, value) => {
			window.localStorage.setItem(name, JSON.stringify(value))
			return window.localStorage[name]
		}
		local_storage.deleteFromLocalStorage = (name) => {
			window.localStorage.removeItem(name)
		}
		local_storage.getFromLocalStorage = (name) => {
			if(name in window.localStorage){
				return JSON.parse(window.localStorage.getItem(name))
			}
			return null
		}
	} else {
		local_storage.local_storage_available = false
		alert('"Recent Searches" functionality will be disabled')
	}

}(window.localStorageService = window.localStorageService || {}, jQuery));