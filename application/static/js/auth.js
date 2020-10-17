$(document).ready(() => {

	(function(auth, $, _) {

		// non-public vars and functions
		let same_site_lax = { SameSite : 'lax' };
		let cookie_properties = { expires: 0.0104167 /* 15 minutes */, SameSite : 'lax' };
		let is_running_settimeout_already = false
		let continue_requesting = true;
		let attempts = 0;

		call_ajax = (properties, return_callback, error_callback, extra_callback, extra_callback_is_timeout, extra_callback_arguments, extra_callback_elements) => {
			if(properties.headers){
				properties.headers = get_auth_header()
			}
			_this = this
			$.ajax(properties).done((data) => {
				if(return_callback && !extra_callback_is_timeout && $.isFunction(return_callback) && !extra_callback_arguments && !extra_callback_elements) return_callback.call(_this, data, extra_callback)
				if(return_callback && !extra_callback_is_timeout && $.isFunction(return_callback) && extra_callback_arguments && extra_callback_elements){
					return_callback.call(_this, data, null)
					extra_callback.call(_this, extra_callback_arguments, ...extra_callback_elements)
				} 
				if(return_callback && $.isFunction(return_callback)) return_callback.call(_this, data, null)
				if(extra_callback_is_timeout){
					if($.isFunction(extra_callback) && !is_running_settimeout_already){
						auth.is_authed_interval = setInterval(extra_callback, 10000); 
						extra_callback.call(_this)
						is_running_settimeout_already = true
					}
				}
			}).fail((error) => {
				error_callback.call(_this, error)
			})
		}

		is_authed = () => {
			call_ajax(
				{
					type: 'GET',
					url: '/api/auth/is_authed/',
					headers: get_auth_header(),
					async: true
				},
				null,
				error_callback,
				null,
				false
			)
		}

		get_auth_header = () => {
			return {
				"Authorization":"Bearer " + auth.token
			}
		}

		token_callback = (data, callback) => {
			Cookies.set('token', data.access_token, cookie_properties)
			auth.token = Cookies.get('token', same_site_lax)
			if($.isFunction(callback)) callback.call(this, data)
		}

		delete_from_storage_callback = () => {
			if(window.localStorageService.local_storage_available) window.localStorageService.setInLocalStorage('logged_in', false)
			clearInterval(auth.is_authed_interval)
		}

		error_callback = (data, callback) => {
			if(data.responseJSON){
				if(data.responseJSON.redirect){
					auth.logout.call(this)
					window.location.href = data.responseJSON.redirect
				} else if(data.responseJSON.detail) {
					if(data.responseJSON.detail.fields){
						for(let field in data.responseJSON.detail.fields){
							let error_message_id = `#${field}_error_message`;
							let error_id = `#${field}_error`;
							$(error_message_id).html(data.responseJSON.detail.fields[field])
							$(error_id).show()
						}
					}
					if(data.responseJSON.detail.should_expire_token){
						window.authService.logout.call(this)
					}
					let error = null
					if(data.responseJSON.detail.detail){
						error = data.responseJSON.detail.detail
					} else if(data.responseJSON.detail && typeof data.responseJSON.detail !== 'object'){
						error = data.responseJSON.detail
					} else if(data.responseJSON.error){
						error = data.responseJSON.error
					}
					if(error){
						auth.$error_message.html(error)
						auth.$error.show()
					}
				}
				if($.isFunction(callback)) callback.call(this, data)
			} else {
				attempts += 1

				if(attempts > 4){
					continue_requesting = false
				}

				auth.$error_message.text("An error occured. We couldn't talk to the server.")
				auth.$error.show()

				if(!continue_requesting){
					clearInterval(auth.is_authed_interval)
				}
			}
		}

		login = (data, callback) => {
			if(data.access_token){
				Cookies.set('token', data.access_token, cookie_properties)
			}
			$('#logged_in_username').text('Logged in as ' + data.username)
			auth.$fav_els.show()
			auth.$logged_in_info.show()
			auth.$login_form.hide()
			$('.alert').hide()
			auth.authed = true
			if(window.localStorageService.local_storage_available)  window.localStorageService.setInLocalStorage('logged_in', true)
			if($.isFunction(callback)) callback.call(this, data)
		}

		data_callback = (data, callback) => {
			auth.$add_email_form_and_password_text.text(data.text)
			if($.isFunction(callback)) callback.call(this, data)
		}
		
		// public vars and functions
		auth.token = Cookies.get('token', same_site_lax);
		auth.is_authed_interval = null;
		auth.authed = null;
		auth.$login_form = $("#login_or_register_form")
		auth.$all_forms = $("#login_or_register_form, #add_email_form, #change_password_form")
		auth.$add_email_form = $("#add_email_form")
		auth.$fav_els = $('.favourite')
		auth.$fav_content = $('#favourite-content')
		auth.$password_and_email_buttons = window.favouritesService.fav_available ? $('#add-email, #change-password, #form_text, #view-favourites') : $('#add-email, #change-password, #form_text');
		auth.$logged_in_info = window.favouritesService.fav_available ? $('#logged_in_username, #log-out, #add-email, #email_form_text, #change-password, #view-favourites') :  $('#logged_in_username, #log-out, #add-email, #email_form_text, #change-password');
		auth.$change_password_form = $('#change_password_form')
		auth.$error = $('#error')
		auth.$error_message = $('#error_message')
		auth.$add_email_form_and_password_text = $('#add_email_form_and_password_text')

		auth.do_action = (action) => {
			switch(action){
				case 'register':
					call_ajax(
						{
							type: 'POST',
							url: '/api/auth/register/',
							data: auth.$login_form.serialize(),
							async: true
						},
						login,
						error_callback,
						null,
						false,
						null,
						null
					)
					break;
				case 'add_email':
					call_ajax(
						{
							type: 'POST',
							url: '/api/auth/add_email/',
							headers: {},
							data: auth.$add_email_form.serialize(),
							async: true
						},
						data_callback,
						error_callback,
						is_authed,
						true,
						null,
						null
					)
					break;
				case 'change_password':
					call_ajax(
						{
							type: 'POST',
							url: '/api/auth/change_password/',
							headers: {},
							data: auth.$change_password_form.serialize(),
							async: true
						},
						data_callback,
						error_callback,
						is_authed,
						true,
						null,
						null
					)
					break;
				default:
					if(!auth.token || auth.token === 'null' || auth.token === 'undefined'){
						call_ajax(
							{
								type: 'POST',
								url: '/api/auth/token/',
								data: auth.$login_form.serialize(),
								async:	true
							},
							token_callback,
							error_callback,
							call_ajax,
							false,
							{
								type: 'GET',
								url: '/api/auth/login/',
								headers: {},
								async: true
							},
							[
								login,
								error_callback,
								is_authed,
								true	
							]
						)
					} else {
						call_ajax(
							{
								type: 'GET',
								url: '/api/auth/login/',
								headers: {},
								async: true
							},
							login,
							error_callback,
							is_authed,
							true,
							null,
							null
						)
					}
					break
			}
		}

		auth.logout = () => {
			delete_from_storage_callback.call(this)
			Cookies.remove('token');
			auth.token = null,
			auth.authed = false
			auth.$logged_in_info.hide()
			auth.$fav_els.hide()
			auth.$add_email_form.hide()
			auth.$login_form.show()
			auth.$login_form[0].reset()
		}
		
	}(window.authService = window.authService || {}, jQuery));

	window.authService.$all_forms.submit(function(event) {
		event.preventDefault();

		let $this_id = $(this).attr('id')

		switch($this_id){
			case 'add_email_form':
				window.authService.do_action('add_email')
				break;
			case 'change_password_form':
				window.authService.do_action('change_password')
				break;
			default:
				window.authService.do_action($('#form_submit').text().toLowerCase())
				break;
		}
	});

	window.authService.$password_and_email_buttons.click(function(){

		let $this_id = $(this).attr('id')
		let multipurpose_modal_header = ''
		let form_submit_text = 'Login'
		let has_account_class = 'has-account'

		switch($this_id){
			case 'form_text':
				if($(this).hasClass(has_account_class)){
					$(this).html('Have an account?<br>No worries<br>Click here to login!')
					$(this).removeClass(has_account_class)
					form_submit_text = 'Register'
				} else {
					$(this).html('No account?<br>No worries!<br>Click here to register!')
					$(this).addClass(has_account_class)
					form_submit_text = 'Login'
				}
				break;
			case 'add-email':
				window.authService.$change_password_form.hide()
				window.authService.$fav_content.hide()
				window.authService.$add_email_form.show()
				multipurpose_modal_header  = 'Changing Email'
				break;
			case 'change-password':
				window.authService.$change_password_form.show()
				window.authService.$add_email_form.hide()
				window.authService.$fav_content.hide()
				multipurpose_modal_header  = 'Changing password'
				break;
			case 'view-favourites':
				window.authService.$change_password_form.hide()
				window.authService.$add_email_form.hide()
				multipurpose_modal_header  = 'Viewing favourites'
				window.favouritesService.handleFavourites('#favourite-content')
				break;
			default:
				break;
		}

		$('#multiPurposeModalHeader').text(multipurpose_modal_header)
		$('#form_submit').text(form_submit_text)
		window.authService.$add_email_form_and_password_text.text('')

	});

	if(window.authService.token){
		window.authService.$login_form.submit()
	}

	// this will fire on 'login' and 'logout'
	if(window.localStorageService.local_storage_available){
		window.addEventListener('storage', (e) => {
			if(window.localStorageService.getFromLocalStorage(e.key) == false){
				switch(e.key){
					case 'logged_in':
						window.location.reload();
						break;
					default:
						window.location.reload();
						break;
				}
			}
		});
	}
});