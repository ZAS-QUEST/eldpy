   HttpRequest httpRequest = HttpRequest.post("https://elar.preservica.com/api/content/search")
        .accept("application/json")
        .contentType("application/x-www-form-urlencoded")
        .header("Preservica-Access-Token", getAccessToken())
        .timeout(300000)
        .query("q", "{ \"q\":\"*\"}")
        .query("start", offset)
        .query("max", 1000)
        .query("metadata", ,
        "xip.size_r_Display,xip.size_r_Preservation,xip.title,xip.document_type,oai_dc.identifier,imdi.mediaFileType,imdi.language,imdi.languageId,imdi.mediaFileFormat");
