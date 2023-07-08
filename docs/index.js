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
	var evt_elm = evt.target || evt.srcElement;
	var elmnt_id = get_att_bu(evt_elm, 'data-toggle_elm_id')
	var toggle_elmnt = document.getElementById(elmnt_id)
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
 * @version 2023-06-17
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @param {Event}
 *                evt
*/
function jump(evt) {

	// window.event => very old IE
	evt = evt || window.event;
	// srcElement => deprecated
	var evt_elm = evt.target || evt.srcElement;
	var elmnt_id = get_att(evt_elm, 'data-jump_elm_id')


	target_elmnt = document.getElementById(elmnt_id)
	if (target_elmnt) {
		parent_element = target_elmnt
		while (parent_element) {
			toggle_elm_id = get_att(parent_element, 'data-toggle_elm_id')
			toggle_elm = document.getElementById(toggle_elm_id)
			if (toggle_elm) {
				toggle_elm.style.display = 'block';
			}

			toggle_icon_id = get_att(parent_element, 'data-toggle_icon_id')
			toggle_icon = document.getElementById(toggle_icon_id)
			if (toggle_icon) {
				toggle_icon.className = "toggle_icon_opened"
			}
			parent_element = parent_element.parentNode
		}

		target_elmnt.scrollIntoView({ block: "start", inline: "nearest", behavior: "smooth" });
	} else {
		console.log("target_elmnt #" + elmnt_id + " not found ")
	}

};
/**
 * Eine Funktion mit einem Element und einem Event registrieren
 *
 * aus: http://www.mediaevent.de/javascript/event_listener.html
 *
 * mehrfach ausführbar => mehrere events (mit obj.onxxxxxxx = ... ist nur *eine* Funktion registrierbar)
 *
 * onmousewheel muss anders registriert werden => Evt.register_wheel_event
 * the_function kann eine Funktionsdefinition oder eine benannte Funktion oder eine einer Variablen zugewisene Funktion sein.
 * Falls das event entfernbar sein soll muss für das Evt.un_register_event eine benannte Funktion oder eine einer Variablen zugewiesene Funktion verwendet werden

 *
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @version 2019-07-10
 *
 * @param {HTMLElement} obj
 * @param {String} event_type ohne "on"
 * @param {Function} the_function
 */
function register_event(dom_element, event_type, the_function) {
	var message_string;
	if (dom_element.addEventListener) {
		// modern browser
		dom_element.addEventListener(event_type, the_function, false);
	} else if (dom_element.attachEvent) {
		// IE <= 8
		dom_element.attachEvent('on' + event_type, the_function);
	} else {
		message_string = "Required javascript-functions addEventListener(...) or attachEvent(...) not available...";
		alert(message_string);
		throw new Error(message_string);
	}
};



/**
 * Check den Browser, immer wieder für Überaschungen gut...
 * 
 * @author Ludwig Kniprath ludwig@kni-online.de
 * 
 * 
 * 
 * @returns {Boolean}
 */
function check_browser() {
	var message_string;

	//attachEvent => old IEs
	if (document.addEventListener || document.attachEvent) {
		return true;
	} else {
		message_string = "Browser-check failed, necessary functions missing! " + " (" + navigator.userAgent + ")";
		alert(message_string);
		throw new Error(message_string);
	}

};


/**
 * modified by @author ${user} last on ${d:date('yyyy-MM-dd HH:mm:ss.SSS')}
 */

/**
 * onload-function, which registers some javascript, if the broowser is capable
 * 
 * 
 * @version 2023-06-17
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @returns void
 */
function init() {
	var toggle_elms, jump_elms, idx
	if (check_browser()) {
		toggle_elms = get_elements_by_attributes(document.body, ['div'], ['data-toggle_icon_id', 'data-toggle_elm_id'])
		for (idx in toggle_elms) {
			elm = toggle_elms[idx]
			toggle_icon_id = get_att(elm, 'data-toggle_icon_id')
			// optional attribute
			initially_open = get_att(elm, 'data-initially_open')
			toggle_icon = document.getElementById(toggle_icon_id)
			if (toggle_icon) {
				if(initially_open){
					toggle_icon.className = "toggle_icon_opened"	
				}else{
					toggle_icon.className = "toggle_icon_closed"
				}
				
				register_event(toggle_icon, 'click', toggle_display)
			} else {
				console.log("toggle_icon #" + toggle_icon_id + " not found ")
			}

			toggle_elm_id = get_att(elm, 'data-toggle_elm_id')
			toggle_elm = document.getElementById(toggle_elm_id)
			if (toggle_elm) {
				if(initially_open){
					toggle_elm.style.display = "block"
				}else{
					toggle_elm.style.display = "none"
				}
			} else {
				console.log("toggle_elm #" + toggle_elm_id + " not found ")
			}
		}

		jump_elms = get_elements_by_attributes(document.body, ['a'], ['data-jump_elm_id'])
		for (idx in jump_elms) {
			register_event(jump_elms[idx], 'click', jump)
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
		// Javascript-Eigenschaft:
		return dom_node[attribute_name];
	} else if (dom_node && dom_node.getAttribute && dom_node.getAttribute(attribute_name) !== null) {
		// HTML-Attribut:
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
	var current_node, found_atts, attribute_value, message_string;
	current_node = event_element;
	found_atts = [];
	while (current_node) {
		attribute_value = get_att(current_node, attribute_name);
		if (attribute_value !== undefined) {
			if (found_atts.length === element_index) {
				return attribute_value;
			}
			found_atts.push(attribute_value);
		}
		current_node = current_node.parentNode;
	}
};

/**
 * returns a list of elements inside dom_node with tag in tag_names and attribute in attribute_names
 * values of attributes optionally taken into account
 * 
 * @author Ludwig Kniprath ludwig@kni-online.de
 * @version 2017-11-30
 * 
 * @param {HTMLElement}
 *            dom_node
 * @param {Array}
 *            tag_names kann auch * enthalten
 * @param {Array}
 *            attribute_names
 * @param {Array}
 *            attribute_values, 
 * 				optional, 
 * 				assigend to attribute_names by index, 
 * 				if index not set in attribute_values than the existance of this attribute is sufficient without consideration
 * @returns {Array}
 */
function get_elements_by_attributes(dom_node, tag_names, attribute_names, attribute_values) {

	var return_elements = [];
	var t_idx, tag_name, tag_elms, elm_idx, elm, att_idx, att_name, att_val, elm_att

	for (t_idx in tag_names) {
		tag = tag_names[t_idx]
		elms = dom_node.getElementsByTagName(tag)

		for (elm_idx in elms) {
			elm = elms[elm_idx]
			att_results = []
			for (att_idx in attribute_names) {
				att_name = attribute_names[att_idx]
				att_val = undefined
				if (attribute_values && att_idx < attribute_values.length) {
					att_val = attribute_values[att_idx]
				}
				elm_att = get_att(elm, att_name)
				att_results[att_idx] = elm_att !== undefined && (elm_att == att_val || att_val == undefined)
			}

			all_atts_result = att_results.length > 0
			for (r_idx in att_results) {
				all_atts_result &= att_results[r_idx]
			}
			if (all_atts_result) {
				return_elements.push(elm);
			}

		}
	}
	return return_elements;
};
