var attrs = {}; 
for (i = 0; i < arguments[0].attributes.length; ++i) { 
  attrs[arguments[0].attributes[i].name] = arguments[0].attributes[i].value 
}
return attrs;