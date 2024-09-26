/**
 * global variable which contains the history of jump_forward calling elements for navigation
 */
var _jump_history = []

/**
 * global variable, index refers to _jump_history, used for "scrolling" through the _jump_history
 */
var _jump_index = 0


/**
 * 1. finds a target-element by its index in _jump_history (global), 
 * 2. toggles display of all recursive parents to 'block' 
 * 3. and scrolls to target-element
 * @version 2024-09-18
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @param {Integer}  jump_index
 */
function jump_to_index(jump_index) {
	if (jump_index >= 0 && jump_index < _jump_history.length) {
		if (_jump_history[jump_index]) {
			let scroll_element = _jump_history[jump_index]
			let parent_element = scroll_element
			while (parent_element) {
				let toggle_elm_id = get_att(parent_element, 'data-toggle_elm_id')
				let toggle_elm = document.getElementById(toggle_elm_id)
				if (toggle_elm) {
					toggle_elm.style.display = 'block';
				}

				let toggle_icon_id = get_att(parent_element, 'data-toggle_icon_id')
				let toggle_icon = document.getElementById(toggle_icon_id)
				if (toggle_icon) {
					toggle_icon.className = "toggle_icon_opened"
				}
				parent_element = parent_element.parentNode
			}
			scroll_element.scrollIntoView({ block: "start", inline: "nearest", behavior: "smooth" });
		}
	} else if (jump_index < 0) {
		_jump_index = 0
	} else {
		_jump_index = _jump_history.length - 1
	}
}
/**
 * jump_to_index(0)
 * @version 2024-09-18
 * @author Ludwig Kniprath ludwig@kni-online.de
 */
function back_to_jump_first() {
	_jump_index = 0
	jump_to_index(_jump_index)

}

/**
 * jump_to_index(_jump_history.length - 1)
 * @version 2024-09-18
 * @author Ludwig Kniprath ludwig@kni-online.de
 */
function back_to_jump_last() {
	_jump_index = _jump_history.length - 1
	jump_to_index(_jump_index)
}

/**
 * jump_to_index(_jump_index - 1)
 * @version 2024-09-18
 * @author Ludwig Kniprath ludwig@kni-online.de
 */
function back_to_jump_back(evt) {
	_jump_index -= 1
	jump_to_index(_jump_index)
}

/**
 * jump_to_index(_jump_index + 1)
 * @version 2024-09-18
 * @author Ludwig Kniprath ludwig@kni-online.de
 */
function back_to_jump_for() {
	_jump_index += 1
	jump_to_index(_jump_index)
}

/**
 * toggles the display of element from none to block
 * toggles the hard-coded class of an +- icon that additionally shows the current state
 * @version 2023-06-17
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @param {Event}
 *                evt
*/
function toggle_display(evt) {
	// window.event => very old IE
	evt = evt || window.event;
	// srcElement => deprecated
	const evt_elm = evt.target || evt.srcElement;
	const elmnt_id = get_att_bu(evt_elm, 'data-toggle_elm_id')
	const toggle_elmnt = document.getElementById(elmnt_id)
	if (toggle_elmnt) {
		if (!toggle_elmnt.style.display || toggle_elmnt.style.display === 'none') {
			toggle_elmnt.style.display = 'block';
			evt_elm.className = "toggle_icon_opened"
		} else {
			evt_elm.className = "toggle_icon_closed"
			toggle_elmnt.style.display = 'none';
		}
	}
};

/**
 * substitute for of <a href...
 * because the internal anchors don't work if the target is hidden (see toggle_display)
 * 1. identify the target-element by attribute "data-jump_elm_id"
 * 2. calls "toggle_display" for all parent elements 
 * 3. scroll to target-element 
 * 4. append the target_element to _jump_history
 * 5. set _jump_index to the last index
 * @version 2023-06-17
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @param {Event}
 *                evt
*/
function jump_forward(evt) {
	const evt_elm = evt.target;
	const elmnt_id = get_att(evt_elm, 'data-jump_elm_id')


	const target_elmnt = document.getElementById(elmnt_id)
	if (target_elmnt) {

		let parent_element = target_elmnt
		while (parent_element) {
			let toggle_elm_id = get_att(parent_element, 'data-toggle_elm_id')
			let toggle_elm = document.getElementById(toggle_elm_id)
			if (toggle_elm) {
				toggle_elm.style.display = 'block';
			}

			let toggle_icon_id = get_att(parent_element, 'data-toggle_icon_id')
			let toggle_icon = document.getElementById(toggle_icon_id)
			if (toggle_icon) {
				toggle_icon.className = "toggle_icon_opened"
			}
			parent_element = parent_element.parentNode
		}
		target_elmnt.scrollIntoView({ block: "start", inline: "nearest", behavior: "smooth" });
		//push both elements to _jump_history, so the user can jump back to the position of the evt_elm and the target_elmnt
		_jump_history.push(evt_elm)
		_jump_history.push(target_elmnt)
		_jump_index = _jump_history.length - 1
	} else {
		alert("target_elmnt #" + elmnt_id + " not found ")
	}

};




/**
 * registers function for event on an element
 *
 *
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @version 2019-07-10
 *
 * @param {HTMLElement} obj
 * @param {String} event_type ohne "on"
 * @param {Function} the_function
 */
function register_event(dom_element, event_type, the_function) {
	if (dom_element.addEventListener) {
		// modern browser
		dom_element.addEventListener(event_type, the_function, false);
	} else if (dom_element.attachEvent) {
		// IE <= 8
		dom_element.attachEvent('on' + event_type, the_function);
	} else {
		//should not happen if check_browser was successfull
		const message_string = "Required javascript-functions addEventListener(...) or attachEvent(...) not available...";
		alert(message_string);
		throw new Error(message_string);
	}
};



/**
 * Browser-Check
 * detect too old versions with lacking javascript-functionality
 * 
 * @author Ludwig Kniprath ludwig@kni-online.de
 * 
 * @returns {Boolean}
 */
function check_browser() {
	//attachEvent => old IEs
	if (document.addEventListener || document.attachEvent) {
		return true;
	} else {
		const message_string = "Browser-check failed, necessary functions missing! " + " (" + navigator.userAgent + ")";
		alert(message_string);
		throw new Error(message_string);
	}

};


/**
 * onload-function, called via onload='init();'
 * registers some javascript, if the browser is capable
 * 
 * 
 * @version 2023-06-17
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @returns void
 */
function init() {
	if (check_browser()) {
		register_event(document.getElementById('back_to_jump_first'), 'click', back_to_jump_first)
		register_event(document.getElementById('back_to_jump_back'), 'click', back_to_jump_back)
		register_event(document.getElementById('back_to_jump_for'), 'click', back_to_jump_for)
		register_event(document.getElementById('back_to_jump_last'), 'click', back_to_jump_last)

		//first jump-target ist the top-Element
		_jump_history.push(document.getElementById('top'))
		_jump_index = _jump_history.length - 1


		const flyout_elements = document.querySelectorAll("sup[data-flyout_id]")
		for (const elm of flyout_elements) {
			let flyout_id = get_att(elm, 'data-flyout_id')
			//get current language from attribute in html-tag
			let language = document.getElementsByTagName('html')[0].getAttribute('lang');
			// two languages implemented
			let flyout_title_de = undefined;
			let flyout_title_en = undefined;
			let inner_html = undefined;
			switch (flyout_id) {
				case 'sup_offset':
					flyout_title_de = "> 0 links \n< 0 rechts\nzur Referenz-Linie in Digitalisier-Richtung"
					flyout_title_en = "> 0 left \n< 0 right\nto reference-line in digitize-direction"
					inner_html = '*1'
					break;
				case 'sup_requires_linestring_m':
					flyout_title_de = "nur bei LinestringM-Referenz-Layer"
					flyout_title_en = "only with LinestringM-reference-layer"
					inner_html = '*2'
					break;
				case 'sup_requires_linestring_z':
					flyout_title_de = "nur bei LinestringZ-Referenz-Layer"
					flyout_title_en = "only with LinestringZ-reference-layer"
					inner_html = '*3'
					break;
				case 'sup_requires_data_layer_editable':
					flyout_title_de = "nur mit editierbarem Datenlayer"
					flyout_title_en = "only with editable data-layer"
					inner_html = '*4'
					break;
				case 'sup_requires_data_feature_selected':
					flyout_title_de = "nur mit selektiertem Datensatz in Feature-Auswahl"
					flyout_title_en = "only with selected feature in feature-selection"
					inner_html = '*5'
					break;
				case 'sup_requires_show_layer':
					flyout_title_de = "nur mit registriertem Show-Layer"
					flyout_title_en = "only with registered Show-Layer"
					inner_html = '*6'
					break;
				case 'sup_snapping':
					flyout_title_de = "Snappingeinstellungen Referenz-Layer:\n  - Erweiterte Konfiguration\n  - Typ 'Segment, Linienendpunkte'\n  - Toleranz 10 Pixel\n(wird automatisch angewendet)"
					flyout_title_en = "Snapping-Configuration for reference-layer:\n  - Advanced Configuration\n  - Type 'Segment, Line-Endpoints'\n  - Tolerance 10 pixels\n(automatically applied)"
					inner_html = '*7'
					break;
				case 'sup_pan_zoom_ctrl_shift':
					flyout_title_de = "[strg-click] ➞ Pan\n[shift-click] ➞ Zoom"
					flyout_title_en = "[ctrl-click] ➞ pan\n[shift-click] ➞ zoom"
					inner_html = '*7'
					break;
				case 'sup_select_unselect_ctrl_shift':
					flyout_title_de = "[click] ➞ vorhandene Layer-Selektion ersetzen\n[strg-click] ➞ aus Selektion entfernen\n[shift-click] ➞ Selektion erweitern"
					flyout_title_en = "[click] ➞ replace current layer-selection\n[ctrl-click] ➞ remove from selection\n[shift-click] ➞ add to selection"
					inner_html = '*8'
					break;
				case 'sup_ctrl_shift_factors':
					flyout_title_de = "[click] ➞ ± 1\n[strg-click] ➞ ± 10\n[shift-click] ➞ ± 100\n[strg + shift-click] ➞ ± 1000"
					flyout_title_en = "[click] ➞ ± 1\n[ctrl-click] ➞ ± 10\n[shift-click] ➞ ± 100\n[ctrl + shift-click] ➞ ± 1000"
					inner_html = '*9'
					break;
				case 'sup_replace_expand_selection_ctrl_shift':
					flyout_title_de = "[strg-click] ➞ Selektion übernehmen\n[shift-click] ➞ Selektion erweitern"
					flyout_title_en = "[ctrl-click] ➞ replace layer selection\n[shift-click] ➞ expand layer selection"
					inner_html = '*10'
					break;
				case 'sup_select_unselect_zoom_ctrl_shift_dbl':
					flyout_title_de = "[click] ➞ select\n[strg-click] ➞ unselect\n[shift-click] ➞ Pan/Zoom\n[dbl-click] ➞ Select + Pan/Zoom"
					flyout_title_en = "[click] ➞ select\n[ctrl-click] ➞ unselect\n[shift-click] ➞ select + pan/zoom\n[dbl-click] ➞ select + Pan/Zoom"
					inner_html = '*11'
					break;
				case 'sup_remove_filter_ctrl':
					flyout_title_de = "Filterdefinition nicht möglich, wenn Layer editierbar\n[strg-click] ➞ Filter entfernen"
					flyout_title_en = "Filter-definition not possible if layer is editable\n[ctrl-click] ➞ remove filter"
					inner_html = '*12'
					break;

				case 'sup_zoom_shift':
					flyout_title_de = "[shift-click] ➞ Zoom"
					flyout_title_en = "[shift-click] ➞ zoom"
					inner_html = '*13'
					break;

				case 'sup_map_select_unselect_ctrl_shift':
					flyout_title_de = "[Punkt klicken oder Rechteck aufziehen] ➞ Kartenselektion\n[Punkt/Rechteck + strg] ➞ aus Selektion entfernen\n[Punkt/Rechteck + shift] ➞ an Selektion anhängen"
					flyout_title_en = "[click point or drag rectangle] ➞ Map-selection\n[point/rectangle + ctrl] ➞ remove from selection\n[point/rectangle + shift] ➞ append to selection"
					inner_html = '*14'
					break;

			}

			if (language == 'de' && flyout_title_de != undefined) {
				elm.title = flyout_title_de

			} else if (flyout_title_en != undefined) {
				elm.title = flyout_title_en
			}

			if (inner_html != undefined) {
				elm.innerHTML = inner_html
			}


		}


		const toggle_elms = document.querySelectorAll("div[data-toggle_icon_id][data-toggle_elm_id]")
		for (const elm of toggle_elms) {
			let toggle_icon_id = get_att(elm, 'data-toggle_icon_id')
			// optional attribute
			let initially_open = get_att(elm, 'data-initially_open')
			let toggle_icon = document.getElementById(toggle_icon_id)
			if (toggle_icon) {
				if (initially_open == '1') {
					toggle_icon.className = "toggle_icon_opened"
				} else {
					toggle_icon.className = "toggle_icon_closed"
				}
				register_event(toggle_icon, 'click', toggle_display)
			} else {
				console.log("toggle_icon #" + toggle_icon_id + " not found ")
			}

			const toggle_elm_id = get_att(elm, 'data-toggle_elm_id')
			const toggle_elm = document.getElementById(toggle_elm_id)
			if (toggle_elm) {
				if (initially_open == '1') {
					toggle_elm.style.display = "block"
				} else {
					toggle_elm.style.display = "none"
				}
			} else {
				console.log("toggle_elm #" + toggle_elm_id + " not found ")
			}
		}

		const jump_forward_elms = document.querySelectorAll('a[data-jump_elm_id],sup[data-jump_elm_id]')
		for (const elm of jump_forward_elms) {
			register_event(elm, 'click', jump_forward)
		}
	}
};

/**
 * gets attribute-value of a node
 * 
 * @version 2023-06-17
 * @author Ludwig Kniprath ludwig@kni-online.de
 * 
 * @param {HTMLElement}
 *            dom_node
 * @param {String}
 *            attribute_name
 * @returns mixed string|undefined
 */
function get_att(dom_node, attribute_name) {

	if (dom_node && dom_node[attribute_name] !== undefined) {
		// Javascript-Property:
		return dom_node[attribute_name];
	} else if (dom_node && dom_node.getAttribute && dom_node.getAttribute(attribute_name) !== null) {
		// HTML-Attribute:
		return dom_node.getAttribute(attribute_name);
	}

};

/**
 * returns attribute-value of parent element
 * 
 * @version 2023-06-19
 * 
 * @param {HTMLElement}
 *            event_element
 * @param {String}
 *            attribute_name
 * @param {Number}
 *            element_index default 0 => first found is returned
 * @returns string
 */
function get_att_bu(event_element, attribute_name, element_index = 0) {
	let current_node = event_element;
	const found_atts = [];
	while (current_node) {
		let attribute_value = get_att(current_node, attribute_name);
		if (attribute_value !== undefined) {
			if (found_atts.length === element_index) {
				return attribute_value;
			}
			found_atts.push(attribute_value);
		}
		current_node = current_node.parentNode;
	}
};

function apply_fly_outs() {

}