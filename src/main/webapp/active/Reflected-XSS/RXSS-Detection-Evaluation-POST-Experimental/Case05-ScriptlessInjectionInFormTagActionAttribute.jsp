<%@ page contentType="text/html; charset=ISO-8859-1" pageEncoding="ISO-8859-1"%><%@ page import="com.nsunina.wavsepenhancement.encoders.HtmlEncoder" %>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>Scriptless Injection in HTML Form Tag Action Attribute scope of the HTML page.</title>
</head>
<body>
<!--
	Contributed by the IronWASP project (http://ironwasp.org/).
	Original Author: Lavakumar Kuppan (lava@ironwasp.org).
-->

<%
if (request.getParameter("userinput") == null || !"POST".equalsIgnoreCase(request.getMethod())) {
%>
	Enter your input:<br><br>
	<form name="frmInput" id="frmInput" method="GET">
		<input type="text" name="userinput" id="userinput"><br>
		<input type=submit value="submit">
	</form>
<%
} 
else {
    try {
	  	    String userinput = request.getParameter("userinput");
			userinput = HtmlEncoder.htmlEncodeAngleBracketsAndQuotes(userinput);
			userinput = userinput.replace(":","");
	  	    out.println("<form action=\"" + userinput + "\">\n"
     			+ "Enter Password: <input name='password' id='password' type='password' value=''/>\n"
     			+ "</form> ");
	  	    out.flush();
    } catch (Exception e) {
        out.println("Exception details: " + e);
    }
} //end of if/else block
%>

</body>
</html>