<%@ page language="java" contentType="text/html; charset=ISO-8859-1"
	pageEncoding="ISO-8859-1"%>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>Case 2 - XXE Injection into intercepted request. Goal: perform XXE injetion to execute a DoS.</title>
    <script>
	    function sendXml()
	    {
		       var xhr = new XMLHttpRequest();
		       xhr.open("POST", "/wavsep/active/XXE/XXE-POST-INTERCEPT-500Error/result-XXE.jsp");
		       var xmlDoc;
		       
		       xhr.onreadystatechange = function() 
		       {
		           if (xhr.readyState == 4 && xhr.status == 200)
		           {
			           document.getElementById("result").innerHTML=xhr.responseText
		           }
		       };
		       
		        xhr.setRequestHeader('Content-Type', 'text/xml');
				var xml="<?xml version=\"1.0\" encoding=\"UTF-8\"?><employees>\n<employee id=\"1\">\n<firstName>Lokesh</firstName>\n<lastName>Gupta</lastName>\n<location>India</location>\n</employee>\n<employee id=\"2\">\n<firstName>Alex</firstName>\n<lastName>Gussin</lastName>\n<location>Russia</location>\n</employee>\n<employee id=\"3\">\n<firstName>David</firstName>\n<lastName>Feezor</lastName>\n<location>USA</location>\n</employee>\n</employees>";
				xhr.send(xml);
	      }
    </script>
</head>

<body>
<h4></h4>
	<form>
		<B>Employees:</B><br><br>
		<script>sendXml();</script>
	</form>
	<div id="result"></div>
	
	<br><br>
</body>
</html>