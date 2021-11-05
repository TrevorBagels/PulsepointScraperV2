function copyText(event, id)
{
  	//stolen from w3schools
	/* Get the text field */
	var copyText = document.getElementById(id);

	/* Select the text field */
	copyText.select();
	copyText.setSelectionRange(0, 99999); /*For mobile devices*/

	/* Copy the text inside the text field */
	document.execCommand("copy");
	notify(event, "Copied!", document.getElementById(id))
}


var notifications = 0


function destroyNotification(id){
	console.log(id)
	document.getElementById(id).remove()
}

function notify(event, text, element){
	var id = notifications.toString();
	var rect = element.getBoundingClientRect();
	var x = event.pageX;
	var y = event.pageY;
	var style = `position: absolute; display:block; z-index: 15; left: ${x}px; top: ${y}px;`
	document.body.innerHTML += `<div style="${style}" class='notification' id="notify${id}">${text}</div>`;
	setTimeout(destroyNotification, 1800, `notify${id}`);
	notifications += 1;
}