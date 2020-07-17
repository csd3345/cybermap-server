[![MIT license](http://img.shields.io/badge/License-MIT-red.svg)](http://opensource.org/licenses/MIT) [![Website dev01-vm.csd.uoc.gr](https://img.shields.io/website-up-down-green-red/http/dev01-vm.csd.uoc.gr.svg)](http://dev01-vm.csd.uoc.gr)

<!-- MADE WITH PYTHON BADGE  -->
<div align="center">
	<a href="https://www.python.org/" alt="made-with-Python"> 
		<img src="http://ForTheBadge.com/images/badges/made-with-python.svg">
	</a>
</div>
<!-- PROJECT LOGO -->
<br />
<div align="center">
    <a href="https://gitlab.com/j3di/cyber-threat-map">
	<img src="https://i.ibb.co/HT2cpRt/logo-transparent.png" alt="logo" border="0" width="250" height="230">    
    </a>
    <h3>
        Real Time Cyber Attack Map
        <br />
        Full Stack Application (client and server)
      </h3>
</div>
<div align="center">
    <a href="https://gitlab.com/j3di/cyber-threat-map">
        <strong>Explore the docs »</strong>
    </a>
    <div>
        ·
        <a href="https://github.com/othneildrew/Best-README-Template">View  Demo</a> ·
        <a href="https://gitlab.com/j3di/cyber-threat-map/issues">Report Bug</a> ·
        <a href="https://gitlab.com/j3di/cyber-threat-map/issues">Request Feature</a> ·
    </div>
</div>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
	* [Built With](#built-with) 
	* [Introduction](#introduction) 
	* [Servers Ecosystem](#servers-ecosystem)
		* [System Schema](#system-schema)
		* [Intercommunication](#intercommunication)
		* [Diagrams](#diagrams)
		* [Components](#components)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
  * [Usage](#usage)
* [Roadmap](#roadmap)
* [License](#license)



<!-- ABOUT THE PROJECT -->
# About The Project
*Note: Project screenshot under construction*
[![Project-Screenshot][project-screenshot]](https://example.com)

## Built With
All the major frameworks that were used to build this project:
* [Python][python]
* [Redis][redis]
* [Tornado][tornado]
* [Mapbox GL JS][mapbox-gl-js]
* [JQuery][jquery]
* [Bootstrap][bootstrap]



## Introduction

There are many great *cyber-attack maps* to track cybersecurity incidents, however, we couldn't find an open-source one that was easily customizable for both *client* and *server*, so we created this enhanced web-application which offers

-   Simultaneous user connections up to 5000
-   Fast data transmission to each user
-   Low RAM usage on the backend
-   Customizable API
-  A full-stack web app

To skip the technical information of the project just jump to the [getting started](#getting-started) section

## User Interface (UI)

Firstly, we need a map to display live cyber-attacks to each connected user. For this, we used [mapbox][mapbox-gl-js], a highly configurable JavaScript library that uses WebGL to render interactive maps. We only have to "feed" the map with the appropriate [GeoJSON data](https://geojson.org/) and the attacks will be displayed. Informational HTML panels were added above the map for statistics or attack descriptions. 

## Servers ecosystem  

For the web-server, we will need a system that can serve requests to many users simultaneously and "feed" each connected user's map with data as mentioned earlier. To achieve that we used [Tornado][tornado]  a scalable, [non-blocking](https://en.wikipedia.org/wiki/Asynchronous_IO) web server and [web application framework](https://en.wikipedia.org/wiki/Web_application_framework) written in [Python][python]. As it is mentioned in their wiki:

> Real-time web features require a long-lived mostly-idle connection per user. In a traditional synchronous web server, this implies devoting one thread to each user, which can be very expensive.
> 
> To minimize the cost of concurrent connections, Tornado uses a single-threaded event loop. This means that all application code should aim to be asynchronous and non-blocking because only one operation can be active at a time.

Tornado is noted for its high performance and its ability to handle a large number of concurrent connections, although it won't be able to also handle real-time [data wrangling][wrangling] and distribution to the users all by itself. This is why we decided to divide the system into *four (4)*  components:


1.  data creation (randomly generated or read from a different source e.g a file or database)  
 2. data [wrangling]
 3. data distribution (to each connected user)
 4.  users traffic handling (initial connection)

These combined form the *servers ecosystem*. 

Of course, no template will serve all projects since needs may differ, nevertheless, this schema increases *security* and *maintainability* of the system and also allow other developers to configure each component more easily without fear of "corrupting" the others.

### System Schema
Each component can be implemented on a separate **server** or **process** or groups of any number of either of those two.  The following table illustrates the implementation of this schema, as well as the aliases that it uses for each component.

| Alias               | Type    | Assigned Components |
|---------------------|---------|---------------------|
| Cyber Map           | Server  | *1* and *4*         |
| Data Proxy          | Server  | *3*                 |
| Attacks Generator   | Process | *2*                 |

*Note:* *Attacks Generator* could be bound as a method on *Data Proxy* instead of a separate program. 

### Components

Data relating to cybersecurity incidents will, in almost all cases, have a common denominator. This is a collection of two distinct IP addresses, one for the origin of the attack and one for the destination of the attack. The port included in these IP addresses is used for recognizing the *type* of the attack. In view of the fact that any extra information regarding a specific cybersecurity incident is optional, it is up to the developer to choose which will be the final form of the data the the users will receive.

 We will refer to this collection as *cyberattack*.

#### Attacks Generator Process
The starting point of the servers ecosystem. Attacks Generator Process is responsible for *Data Creation* or *Data Generation* is the process of making cyberattacks available to the system. These data are, for now, in preliminary form *(e.g simple IP addresses with ports)* but this was intendent to keep them as simple as possible. 

Following the system's schema this component is implemented with a simple process. This process could be a script programmed in any [scripting-language](https://en.wikipedia.org/wiki/Scripting_language) therefore a Python script was used in order to reduce the complexity of the overall project by not using multiple programming languages.

#### Users Traffic Handling




### Intercommunication

Intercommunication between the components is handled by [Redis][redis] and specifically by its [Pub/Sub feature][redis-pub-sub].

This feature implements the [Publish–subscribe pattern][pub_sub_pattern] which offers great speed and roughly any memory consumption even when there are thousands of data transactions per second. This particular concept allows us to send data fast between components.

Following the two servers and one process schema as described earlier, we can define which *Redis' channels* will be used and which component will be *listener/receiver* or *both*.
The two Redis' channels are
-   raw-cyberattacks
-   cyberattacks

#### *raw-cyberattacks* Channel
The component responsible for publishing data on this channel determines the initial functionality that will be used to obtain those particular data. These could be randomly generated, read from a file/database or received from an external source.

#### *cyberattacks* Channel
Data published on this channel must be in the final form because these data are what users receive.

### Diagrams
Following a diagram of the components' intercommunication as demonstrated:

![servers-ecosystem][servers-ecosystem-diagram]

Jumping into more details the system performs *five* steps before completing an adequate cycle. One completed cycle corresponds to one "ready-to-be-transfered" cyberattack. The system may operate indefenetly without any connected user to "consume" the cyberattacks.

![servers-ecosystem-explained][servers-ecosystem-details-diagram]

1.  *Attacks Generator Process* starts to **produce** cyberattacks and publishes them to *raw-cyberattacks channel*.
2.  *Data Proxy Server* is **listening** on the raw-cyberattacks channel 
3. When *Data Proxy Server* **receives** data it forges them into the desired final form and then publishes them to *cyberattacks channel*.
4.  Cyber Map Server is **listening** on the *cyberattacks channel* 
5. When Cyber Map Server **receives** data it forwards them to all *connected users.*

## Roadmap

See the [open issues][project-issues] for a list of proposed features (and known issues).

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.




<!--  Links for better information management -->
[project-home]: https://gitlab.com/j3di/cyber-threat-map
[project-issues]: https://gitlab.com/j3di/cyber-threat-map/issues
[project-screenshot]: https://i.ibb.co/bdZW8mG/project-screenshot.png

[servers-ecosystem-diagram]: https://i.ibb.co/5rX3bQF/servers-ecosystem.png
[servers-ecosystem-details-diagram]: https://i.ibb.co/9WwCZHk/servers-ecosystem-details.png




[tornado]: https://www.tornadoweb.org/en/stable/index.html
[redis]: https://redis.io/topics/introduction
[redis-pub-sub]: https://redis.io/topics/pubsub
[bootstrap]: https://getbootstrap.com/
[python]: https://www.python.org/
[jquery]: https://jquery.com
[mapbox-gl-js]: https://docs.mapbox.com/mapbox-gl-js/api/


[pub_sub_pattern]: https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern
[wrangling]: https://en.wikipedia.org/wiki/Data_wrangling
