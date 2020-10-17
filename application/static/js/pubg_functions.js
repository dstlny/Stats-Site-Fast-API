window.player_aliases = []

$(document).ready(() => {

	// disable errors...
	$.fn.dataTable.ext.errMode = 'none';

	const $datatable_container = $('#datatable_container');
	const $card_container = $('#card_container');

	(function(pubg, $, _) {

		// private vars and functions
		let endpoints = window.endpoints;
		let table_rosters = {};
		let ranked_showing = false;
		let cards = [];
		let child_rows = [];
		let season_stats_requested = false;

		getPlayerName = () => {
			return document.getElementById("player_name").value
		}

		getPlatform = () => {
			return document.getElementById('id_platform').value
		}

		getPlayerId = () => {
			return document.getElementById('player_id').value
		}

		getGameMode = () =>  {
			return document.getElementById('id_game_mode').value
		}

		getPerspective = () =>  {
			return document.getElementById('id_perspective').value
		}
		
		getMatchesEndpoint = () =>  {
			return endpoints.retrieve_matches
		}

		getSeasonsEndpoint = () =>  {
			return endpoints.retrieve_player_stats
		}

		getGameModeFilter = (game_mode, perspective) => {

			game_mode = game_mode == 'all' ? null : game_mode
			perspective = perspective == 'all' ? null : perspective

			if(!game_mode && !perspective){
				return
			}

			if(game_mode){

				if(perspective && game_mode !== 'tdm'){
					return `${game_mode}-${perspective}`
				} else {
					return `${game_mode}`
				}

			} else {
				if(perspective){
					return `${perspective}`
				}
			}

		}

		formatChildRow = (id) => {
			let generated_datatable_id = `rosters_datatable_${id}`
		
			let generated_row_data = `
				<div class="col-md-12" style='padding: 10px;' id='${generated_datatable_id}_wrapper'>
					<table class='table table-sm' id='${generated_datatable_id}' style='width: 100%'>
						<thead>
							<tr>
								<th width='20%%'>Rank</th>
								<th width='80%'>Team Details</th>
							</tr>
						</thead>
						<tbody>
						</tbody>
					</table>
				</div>
			`
		
			return {
				datatable_id: generated_datatable_id,
				html: generated_row_data
			}
		}

		formatRosterCardTable = (data) => {
			let generated_table_rows = []
			generated_table_rows.push(`
			<div class='col-md-12'>
				<table class="table table-bordered">
					<thead>
						<tr>
							<th class='card-header text-center'>Name</th>
							<th class='card-header text-center'>Kills</th>
							<th class='card-header text-center'>Damage</th>
						</tr>
					</thead>
					<tbody>
			`)
				
			for (let i=0, len=data.length; i < len; i++){
				generated_table_rows.push(`
					<tr>
						<td class='text-center'>${data[i].player_name}</td>
						<td class='text-center'>${data[i].kills}</td>
						<td class='text-center'>${data[i].damage}</td>
					</tr>
				`)
			}
			generated_table_rows.push(`
					</tbody>
				</table>
			</div>`)
			
			return generated_table_rows.join('')
		
		}

		getRosterForMatch = (match_id, datatable_id) => {

			if(!table_rosters[datatable_id]){
				
				let roster_table = $(`#${datatable_id}`).DataTable({
					columns: [
						{ data: 'roster_rank', width: '15%' }, // rank
						{ data: 'participant_objects', width: '85%' }, // rosters
					],
					order: [[ 0, "asc" ]],
					createdRow(row, data, _){
						const is_alias = window.player_aliases.find(alias => data.participant_objects.includes(alias))
						if(is_alias) data.roster_rank == 1 ? $(row).addClass('table-success') : $(row).addClass('table-info')
					},
					scrollY: "200px",
					scrollCollapse: true,
					paging: false
				});

				table_rosters[datatable_id] = {
					actual_data: [],
					datatable: roster_table,
				}

				$(`#${datatable_id}`).LoadingOverlay("show");

				let json_data = {
					api_id: getPlayerId(),
					match_id: match_id
				}
			
				$.ajax({
					data: JSON.stringify(json_data),
					type: 'POST',
					dataType: 'json',
					url: endpoints.match_rosters
				}).done((data) => {
					let rosters = data
					for (let i = 0, len=rosters.length; i < len; i++){						
						table_rosters[datatable_id].actual_data.push({
							roster_rank: rosters[i].roster_rank,
							participant_objects: rosters[i].participant_objects,
						})
					}
					table_rosters[datatable_id].datatable.rows.add(table_rosters[datatable_id].actual_data).draw(false)
					$(`#${datatable_id}`).LoadingOverlay("hide", true);
				}).fail((_) => {
					checkDown()
				})
			} else {
				let roster_table = $(`#${datatable_id}`).DataTable({
					data: table_rosters[datatable_id].datatable.rows().data(),
					columns: [
						{ data: 'roster_rank', width: '15%' }, // rank
						{ data: 'participant_objects', width: '85%' }, // rosters
					],
					createdRow(row, data, _){
						const is_alias = window.player_aliases.find(alias => data.participant_objects.includes(alias))
						if(is_alias) data.roster_rank == 1 ? $(row).addClass('table-success') : $(row).addClass('table-info')
					},
					order: [[ 0, "asc" ]],
					scrollY: "200px",
					scrollCollapse: true,
					paging: false
				});
				roster_table.draw(false);
				table_rosters[datatable_id].datatable = roster_table    
			}
		}

		checkDown = () => {
			$.ajax({
				type: 'GET',
				url:'/api/common/status/',
			}).done((data) => {
				down = data.backend_status == true
			});
		}

		initTimer = (millisecond_till_refresh) => {
			let $countdown = $('#countdown')
			let future = moment.unix(millisecond_till_refresh).utc()

			let inter = setInterval(() => {
				let duration = moment.duration(future - moment().utc(), 'milliseconds');
				let hours = duration.hours()
				let minutes = duration.minutes()
				let seconds = duration.seconds()

				if(hours <= 0 && minutes <= 0 && seconds <= 0){
					$countdown.text("Refreshing...")
					pubg.table.ajax.reload()
					clearInterval(inter)
				} else {
					$countdown.text(hours + " Hour(s), " + minutes + " Minute(s) and " + seconds + " Second(s) until this player is refreshed.")
				}
			}, 1000);
		}

		// public vars and functions
		pubg.table = $('#results_datatable').DataTable({
			ajax: {
				type: 'POST',
				data: (_) => {
					return JSON.stringify({
						api_id: getPlayerId(),
						player_name: getPlayerName()
					});
				},
				url: getMatchesEndpoint(),
				error: (xhr, _, __) => {
					if(xhr.status >= 400 && xhr.status <= 404){
						pubg.table.settings()[0].jqXHR.abort()
						$('.dataTables_empty').text('No matches to fetch for this user.')
					} else {
						checkDown()
					}
				},
				dataSrc: (json) => {
					return json.data
				}
			},
			createdRow: (row, data, _) => {
				// set the ID of the row, to the id of the match
				row.id = data.id
			},
			fnInitComplete: (_, json) => {
				initTimer(json.next_refreshes)
				
				let json_data = json.data
				let player_aliases = json.player_aliases
				
				for (let i = 0, len=player_aliases.length; i < len; i++){
					if(!(window.player_aliases.includes(player_aliases[i]))){
						window.player_aliases.push(player_aliases[i])
					}
				}

				if(json_data){
					$('#seasons_container').show();
					let raw_mode, team_details_object, current_player, cards_list, templates, elements;

					for (let i = 0, len=json_data.length; i < len; i++){

						raw_mode = json_data[i].raw_mode
						team_details_object = json_data[i].team_details_object
						current_player = team_details_object.find(player => {
							return player_aliases.includes(player.player_name)
						})

						card = {
							date_created: json_data[i].date_created.timestamp,
							template: `
							<div class="col-md-4 roster_card" data-game-mode="${raw_mode.toLowerCase()}" style='margin-bottom: 15px;'>
								<div class="card shadow-sm">
									<div class="card-header">
										<span class='float-sm-left'>${json_data[i].map}</span>
										<small class="float-sm-right">${json_data[i].time_since}</small>
									</div>
									<div class="card-body" style='padding: 20px'>
										<div class='row'>
											<a role="button" style='margin-left: 15px; margin-right: 15px' href="${json_data[i].btn_link}" class='btn btn-primary btn-block stretched-link'>View match</a>
										</div>
										<div class='row top-buffer'>
											<div class='col-md-6'>
												<span class="w-100 badge badge" style='padding: 20px; margin:0px; background-color: #f5f5f5'>
													<h6>Place<br>${json_data[i].team_placement}</h6>
												</span>
											</div>
											<div class='col-md-6'>
												<span class="w-100 badge badge" style='padding: 20px; margin:0px; background-color: #f5f5f5'>
													<h6>Kills<br><b>${current_player.kills || 0}</b></h6>
												</span>
											</div>
										</div>
										<div class='detailed' style=''>
											<div class='row top-buffer'>
												<div class='col-md-12'>
													<table class="table table-bordered">
														<tbody>
															<tr>
																<th class='card-header' width='40%'>Date Created</th>
																<td class='card-body'>${json_data[i].date_created.display}</td>
															</tr>
															<tr>
																<th class='card-header' width='40%'>Mode</th>
																<td class='card-body'>${json_data[i].mode}</td>
															</tr>
														</tbody>
													</table>
												</div>
											</div>
											<div class='row top-buffer'>
												${formatRosterCardTable(team_details_object)}
											</div>
										</div>
									</div>
								</div>
							</div>
						`
						}
						cards.push(card)
					}

					// sort them by date
					cards_list = cards.sort((a,b) => {
						// Turn your strings into dates, and then subtract them
						// to get a value that is either negative, positive, or zero.
						return b.date_created - a.date_created
					});	

					// remove all the current cards
					$('.roster_card').remove()

					templates = []
					// create them, in the correct order
					for (let cards_i = 0, cards_len=cards_list.length; cards_i < cards_len; cards_i++){
						templates.push(cards_list[cards_i].template)
					}
					$('#card_container_row').html(templates.join(''))

					if(pubg.matches_as_cards){
						$('#as_detailed_cards').click()
					}

					elements = []
					// re-open previously opened rows pre refresh
					for (let i = 0, len=child_rows.length; i < len; i++){
						elements.push('#' + child_rows[i] + ' td.details-control');
					}

					$(elements.join(', ')).trigger('click');
				}
				
			},
			columns: [
				{ 
					className: 'details-control',
					orderable: false,
					data: null,
					defaultContent: '',
					width: '2%'  
				},
				{ data: 'map', width: '2%' }, // map
				{ data: {
						_: 'mode',
						sort: "raw_mode"
					},
					width: '2%' 
				}, // mode
				{ data: {
						_: "date_created.display",
						sort: "date_created.timestamp"
					}, // created,
					width: '2%'
				},
				{ data: 'team_placement', width: '2%' }, // placement
				{ data: 'team_details', width: '20%' }, // details
				{ data: 'actions', width: '2%' }, // actions
			],
			pageLength: 25,
			filter: true,
			deferRender: true,
			order: [[ 4, "desc" ]],
			language: {
				zeroRecords: "No matches to display for this user...",
				loadingRecords: "Loading matches for user..."
			}
		});

		// Add event listener for opening and closing details
		pubg.table.on('click', 'td.details-control', function () {
			const tr = $(this).closest('tr');
			const id = tr[0].id
			const idx = $.inArray(id, child_rows);
			const row = pubg.table.row(tr);

			const returned_obj = formatChildRow(id)
			const datatable_id = returned_obj.datatable_id
			const html = returned_obj.html

			if (row.child.isShown()) {
				row.child.hide();
				tr.removeClass('shown');
				child_rows.splice(idx, 1);
			} else {
				row.child(html).show();
				getRosterForMatch(id, datatable_id)
				tr.addClass('shown');

				if (idx === -1) {
					child_rows.push(id)
				}
			}
		});

		pubg.filterResults = () => {
			const game_mode = getGameMode();
			const perspective = getPerspective();
			const filter = getGameModeFilter(game_mode, perspective);
			const $not_matching_criteria_message = $('#not_matching');

			if(filter){

				const $cards_not_matching_filter  = $(`.roster_card:not([data-game-mode*='${filter}'])`);
				const $cards_matching_filter = $(`.roster_card[data-game-mode*='${filter}']`);

				if(pubg.matches_as_cards){
					$datatable_container.hide()
					$card_container.show()

					if($cards_matching_filter.length >= 1){
						$not_matching_criteria_message.hide()
						$cards_not_matching_filter.hide()
						$cards_matching_filter.show()
					} else {
						$not_matching_criteria_message.show()
						$cards_not_matching_filter.hide()
						$cards_matching_filter.hide()
					}

				} else {
					$datatable_container.show()
					$card_container.hide()
					pubg.table.columns(2).search(filter).draw(false);
				}
			} else {
				$not_matching_criteria_message.hide()
				pubg.table.search('').columns().search('').draw(false);
				if(pubg.matches_as_cards){
					$datatable_container.hide()
					$card_container.show()
				} else {
					$datatable_container.show()
					$card_container.hide()
				}
			}

			pubg.seasonStatToggle(perspective)
		}
		

		pubg.seasonStatToggle = (perspective) => {
	
			switch(perspective){
				case 'fpp':
					$('#tpp_row, #ranked_tpp_row').hide()
					$(`#${ranked_showing ? 'ranked_' : ''}fpp_row`).show()
					break;
				case 'tpp':
					$('#fpp_row, #ranked_fpp_row').hide()
					$(`#${ranked_showing ? 'ranked_' : ''}tpp_row`).show()
					break;
				default:
					$(`#${ranked_showing ? 'ranked_' : ''}tpp_row, #${ranked_showing ? 'ranked_' : ''}fpp_row`).show()
					break;
			}

		}

		pubg.retrievePlayerSeasonStats = () => {
			
			if(season_stats_requested) return

			let $season_stats = $(`#season_stats`)
		
			$season_stats.LoadingOverlay("show");

			let json_data = {
				api_id: getPlayerId(),
				platform: getPlatform()
			};
			
			$.ajax({
				data: JSON.stringify(json_data),
				type: 'POST',
				dataType: 'json',
				url: getSeasonsEndpoint()
			}).done((data) => {

				for (let i = 0, len=data.length; i < len; i++){
					for(let key in data[i]){
						if(key !== 'container' && key !== 'text' && key !== 'keys'){
							document.getElementById(key).innerHTML = data[i][key]
						} else {
							if(key == 'container'){
								$(`#${data[i].container}`).LoadingOverlay("show", {
									background: "rgba(255, 255, 255, 1)",
									image: false,
									fontawesome: `fa fa-exclamation-circle`,
									fontawesomeAutoResize: true,
									text: `${data[i].text}`,
									textAutoResize: true,
									size: 40,
									maxSize: 40,
									minSize: 40
								});
							}
						}
					}
				}

				$season_stats.LoadingOverlay("hide", true);
				season_stats_requested = true
			}).fail((_) => {
				checkDown()
			});
	
		}

		pubg.matches_as_cards = false;

	}(window.pubg = window.pubg || {}, jQuery));

	$('#as_table, #as_detailed_cards, #as_compact_cards, #id_game_mode, #id_perspective').on('click', function (event) {

		let id = $(this).attr('id')

		let $detailed = $('.detailed')

		if(id.includes('table')){
			window.pubg.matches_as_cards = false;
			$datatable_container.show();
			$card_container.hide();
			window.pubg.table.draw(false);
		} else if(id.includes('detailed')){
			window.pubg.matches_as_cards = true;
			$datatable_container.hide();
			$detailed.show();
			$card_container.show();
		} else if(id.includes('compact')){
			window.pubg.matches_as_cards = true;
			$datatable_container.hide();
			$detailed.hide();
			$card_container.show();
		} else if(id.includes('perspective') || id.includes('game_mode')){
			window.pubg.filterResults()
		}
	});
	
	$("#season_stats_button").click(() => {
		window.pubg.retrievePlayerSeasonStats()
	});
});