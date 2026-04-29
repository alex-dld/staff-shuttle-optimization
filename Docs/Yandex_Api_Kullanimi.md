Quick start
Get a key for the JavaScript API and Geocoder HTTP package.

Note

Key activation takes up to 15 minutes.

Send request:

Request for “Mohammed Bin Rashid Boulevard 1”:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=Mohammed+Bin+Rashid+Boulevard+1&lang=en_US&format=json

Request with the coordinates of the building located at “Mohammed Bin Rashid Boulevard 1”:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=25.197300,55.274243&lang=en_US&format=json

How can we improve the documentation?
Describe your experience and problems you had



Request format
All params
https://geocode-maps.yandex.ru/v1
  ? apikey=<string>
  & geocode=<string>
  & lang=<string>
  & [kind=<string>]
  & [rspn=<boolean>]
  & [ll=<number>,<number>]
  & [spn=<number>,<number>]
  & [bbox=<number>,<number>~<number>,<number>]
  & [results=<integer>]
  & [skip=<integer>]
  & [uri=<string>]
  & [format=<string>]

apikey
Required parameter

The key issued in the Developer's Dashboard.

Note

Key activation takes up to 15 minutes.

geocode
Required parameter

Address or coordinates of the object being searched for. The specified data determines the type of geocoding:

If an address is specified, it is converted to object coordinates. This process is called forward geocoding.
If coordinates are specified, they are converted to the object's address. This process is called reverse geocoding.
Several formats for entering coordinates are available.

lang
Required parameter

Language of the response and regional settings of the map.

Record format lang=language_region, where:

language — Two-letter language code. Specified in ISO 639-1 format. Sets the language for displaying the names of geographical features.
region — Two-letter country code. Specified in ISO 3166-1 format. Determines regional settings.
List of supported values:

ru_RU — Russian
uk_UA — Ukrainian;
be_BY — Belarusian
en_RU — response in English, Russian map features;
en_US — response in English, American map features;
tr_TR — Turkish (only for maps of Türkiye).
If the parameter has a locale value that is not in this list, the service selects the language closest to the one set.

Example: lang=uk_UA.

sco
Only if the geocode parameter sets the coordinates. Order of coordinates.

Possible values:

longlat — Longitude, latitude.
latlong — Latitude, longitude.
Default value: longlat.

kind
Only if the geocode parameter sets the coordinates. The type of required toponym. List of accepted values:

house — house
street — street
metro — subway station
district — city district
locality — locality (city, town, village, etc.)
If omitted, the API will choose the toponym type automatically.

rspn
Flag indicating whether the search scope should be restricted to the specified area. The area is defined by the ll and spn or bbox parameters. Possible values:

0 — Do not restrict search.
1 — Restrict search.
Default value: 0.

Note

If the geocode parameter sets the coordinates, the rspn parameter is ignored.

ll
Longitude and latitude of the center of the search area. The span of the search area is set in the spn parameter.

spn
The span of the search area. The center of the area is set in the ll parameter.
Set by two numbers:

the first is the difference between the maximum and minimum longitude of the area;
the second is the difference between the maximum and minimum latitude.
Note

If the geocode parameter sets the coordinates and the kind parameter value is district, the spn parameter is ignored.

bbox
An alternative method for setting the search area.

The borders are defined as the geographical coordinates of the lower-left and upper-right corners of the area (in the order "longitude, latitude").

Record format: bbox=x1,y1~x2,y2

Note

If bboxand ll+spn are used simultaneously, the bbox parameter takes priority.

Ignored if the geocode parameter sets the coordinates.

format
Geocoder's response format — json

results
Maximum number of objects to be returned. If the skip parameter is set, its value must be set explicitly.

Default value: 10.

Maximum value: 50.

skip
The number of objects to skip in the response, starting from the first one. If this parameter is set, the results parameter must also be set. The value of the skip parameter must divide evenly by the value of the results parameter.
Default value: 0.

uri
Additional information about the object. The parameter value is returned in the Geosuggest response. To use it in a request, specify a value instead of text and coordinates.

Format for geographical coordinates in the request
Geographical coordinates in the geocode parameter are set sequentially in one of the following formats:

Record format	Order of coordinates	Example
+-float, +-float	Longitude, latitude	134.854, -25.828
float [direction], float [direction]*	Any	E134.854, S25.828 134.854E, 25.828S
+-deg° mm' ss", +-deg° mm' ss"	Latitude, longitude	-25°49′41.1″, 134°51′15.88″
deg° mm' ss" [direction], deg° mm' ss" [direction]*	Any	25°49′41.1″S, 134°51′15.88″E
NMEA	Any	2549.67,S, 13451.26,E
* [direction] - The letter designation of one of the four directions: N, E, W, S. - Spaces are allowed between letters and coordinates.

Spaces, commas, or semicolons can be used as delimiters. Spaces are allowed on either side of the delimiter character.

Note

The ";" character should be encoded as "%3B".

How can we improve the documentation?
Describe your experience and problems you had



https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=Dubai, Mohammed Bin Rashid Boulevard, 1&lang=en_US&format=json

In this case, the geocoder response will look like this:

Response params
response
Geocoder's response.

GeoObjectCollection
Main collection of geo objects.

metaDataProperty
Metadata of the collection of geo objects.

GeocoderResponseMetaData
Information about the request and the number of toponyms found. Inside this object there can be fields:

fix – a character corrected by the spelling service.
request – requested address.
suggest – variant of response corrected by the correction service.
found – number of toponyms found.
results – number of requested search results.
skip – shows how many results to skip in the service response (from the beginning of the list).
featureMember
List of geo objects.

GeoObject
The geo object collection.

metaDataProperty
Geo object metadata.

GeocoderMetaData
Detailed information about the toponym found. There can be fields inside:

kind – type of toponym found.

precision – house match precision in request and response.

text – full address of the object in one line of text.

Address – information about the found object. There can be fields inside:

country_code — country code in the format ISO 3166-1.
formatted — the address of a toponym in one line.
Components — the address of a toponym divided into components. The components are represented by a pair of values kind and name and are organized in descending order from the largest to the smallest (for example, from country to house).
Warning

The AddressDetails field is obsolete. The Address field is used instead. It displays the complete address of the object in hierarchical order (country, region, city, district, street, house, building).

name
The text that is recommended to be specified as a title when displaying the found object.

description
The text that is recommended to be specified as a subtitle when displaying the found object.

boundedBy
The boundaries of the area in which the company belongs. Contains the coordinates of the lower left and upper right corners of the area. The coordinates are listed in the sequence "longitude, latitude".

uri
ID of the found object.

Point.pos
Coordinates of the geo object.

Coordinates of the request in the geocoder's response
The geocoder returns the given coordinates in the metaDataProperty.GeocoderResponseMetaData.Point.pos field. Coordinates are displayed in the format "[longitude] [latitude]":

{
  "GeocoderResponseMetaData": {
    "request": "E134.854,S25.828",
    "found": "1",
    "results": "10",
    "Point": {
      "pos": "134.854412 -25.828084"
    }
  }
}

Order of results
For direct geocoding (the coordinates are determined using the address and/or name), the results are sorted according to their similarity to the address or name specified in the request.
For reverse geocoding (the address is determined from the coordinates), the results are sorted according to the size of the geometric area that the object belongs to, in reverse order (house number, street, district, city, and so on).
Error messages
Code	Description
400	The request is missing a required parameter or an invalid parameter value is specified. The message contains additional information about the error.
403	The request contains an invalid apikey.
429	There are too many requests in a short time.
If an error occurs while processing a request, API returns a message with the error description in the message field.

Examples:

{
    "statusCode": 400,
    "error": "Bad Request",
    "message": "Parameter \"geocode\": \"geocode\" is not allowed to be empty"
}

{
    "statusCode": 400,
    "error": "Bad Request",
    "message": "\"Request\" must contain at least one of [geocode, uri]"
}

{
    "statusCode": 400,
    "error": "Bad Request",
    "message": "Missing apikey"
}

{
    "statusCode": 403,
    "error": "Forbidden",
    "message": "Invalid apikey"
}

How can we improve the documentation?
Describe your experience and problems you had


Examples
Basic search by address
A request for “Mohammed Bin Rashid Boulevard 1”:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=Mohammed+Bin+Rashid+Boulevard+1&lang=en_US&format=json

Basic search by coordinates
Request with the coordinates of the building located at “Mohammed Bin Rashid Boulevard 1”:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=55.270141,25.193445&lang=en_US&format=json

A request with a spelling error
A request with the spelling error “Burj-Halifa”, corrected in the response:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=Burj-Halifa&lang=en_US&format=json

Search for objects in a specified area
If the request specifies the search area, the results will show objects that are closest to this area first. For example:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=Dubai+Marina&ll=25.080549,55.136670&spn=3.552069,2.400552&lang=en_US&format=json

Restricting the number of results in the response
Some requests may match multiple objects. In the geocoder request, the desired amount of objects to output can be specified, as well as the number of the first one of them.

Request for “Dubai Marina” - first 5 results:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=Dubai+Marina&results=5&lang=en_US&format=json

Request for “Dubai Marina” - 5 results, starting from the 11th:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=Dubai+Marina&results=5&skip=10&lang=en_US&format=json

Request with the toponym type specified
A search for the metro station that is closest to the coordinates:

https://geocode-maps.yandex.ru/v1/?apikey=YOUR_API_KEY&geocode=25.080549,55.136670&kind=metro&results=1&lang=en_US&format=json

How can we improve the documentation?
Describe your experience and problems you had
