var attrs = {}; 
for (i = 0; i < arguments[0].attributes.length; ++i) { 
  attrs[arguments[0].attributes[i].name] = arguments[0].attributes[i].value 
}
var viewport;
try{
	// second argument present
	// if arguments[1] == true, return the viewport size
	if(arguments[1]){
		// get the total dimension of an element: https://stackoverflow.com/questions/1145850/how-to-get-height-of-entire-document-with-javascript
		var body = document.body, html = document.documentElement;
		var height = Math.max( body.scrollHeight, body.offsetHeight, 
							   html.clientHeight, html.scrollHeight, 
							   html.offsetHeight );
		var width = Math.max( body.scrollWidth, body.offsetWidth, 
							  html.clientWidth, html.scrollWidth, 
							  html.offsetWidth );
		viewport = [height, width];
		return [attrs, viewport];
	} else {
		return attrs;
	}
	
}catch(err){
	// second argument not present
	return attrs;
}
