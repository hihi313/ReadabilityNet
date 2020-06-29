var node = arguments[0].childNodes;
var arr = [];
for(var i = 0; i < node.length; i++){
	var ni = node[i];
	if(ni.nodeType == 3){//text node
		var str = ni.data.replace(/\s+/g, " ");
		if(str.length <= 1){
			//pass
		}else{
			arr.push(str)//just store the plain text value
		}
	}else if(ni.nodeType == 1){//element node
		if(ni.tagName == "SCRIPT" || ni.tagName == "STYLE" || ni.tagName == "LINK" || ni.tagName == "NOSCRIPT"){
			//pass
		}else{
			arr.push(ni);
		}
	}
}
return arr;