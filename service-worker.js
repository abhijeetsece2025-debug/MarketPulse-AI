const CACHE_NAME =
    "marketpulse-ai-v3";


const APP_SHELL = [

    "/",

    "/manifest.json",

    "/icons/launchericon-48x48.png",

    "/icons/launchericon-72x72.png",

    "/icons/launchericon-96x96.png",

    "/icons/launchericon-144x144.png",

    "/icons/launchericon-192x192.png",

    "/icons/launchericon-512x512.png"

];


/* =========================================================
   INSTALL
========================================================= */

self.addEventListener(
    "install",
    function (event) {

        event.waitUntil(

            caches
                .open(CACHE_NAME)
                .then(
                    function (cache) {

                        return cache.addAll(
                            APP_SHELL
                        );

                    }
                )

        );


        self.skipWaiting();

    }
);


/* =========================================================
   ACTIVATE
========================================================= */

self.addEventListener(
    "activate",
    function (event) {

        event.waitUntil(

            caches
                .keys()
                .then(
                    function (cacheNames) {

                        return Promise.all(

                            cacheNames
                                .filter(
                                    function (name) {

                                        return (
                                            name !==
                                            CACHE_NAME
                                        );

                                    }
                                )
                                .map(
                                    function (name) {

                                        return caches.delete(
                                            name
                                        );

                                    }
                                )

                        );

                    }
                )

        );


        self.clients.claim();

    }
);


/* =========================================================
   FETCH
========================================================= */

self.addEventListener(
    "fetch",
    function (event) {

        /*
           Only GET requests.
        */

        if (
            event.request.method !==
            "GET"
        ) {

            return;

        }


        const url =
            new URL(
                event.request.url
            );


        /*
           Only handle requests
           from our own application.
        */

        if (
            url.origin !==
            self.location.origin
        ) {

            return;

        }


        /*
           Network first.

           This is important for:
           - stock prices
           - predictions
           - news
           - updated JavaScript
           - updated HTML

           If internet is unavailable,
           cached content is used.
        */

        event.respondWith(

            fetch(
                event.request
            )
            .then(
                function (response) {

                    return response;

                }
            )
            .catch(
                function () {

                    return caches.match(
                        event.request
                    );

                }
            )

        );

    }
);