/**
 * Main module.
 */
angular.module('Tweetement', ['ui.router', 'ngSanitize'])
    .config(['$stateProvider', '$urlRouterProvider',
    function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise("/");

        $stateProvider
            .state('index', {
                url: "/",
                templateUrl: "assets/partials/main.html",
                controller: 'MainCtrl'
            })
            .state('result', {
                url: "/result/{qid:\\d+}",
                templateUrl: "assets/partials/result.html",
                controller: 'ResultCtrl'
            })
    }]);


/**
 * Directive that generates a Twitter status-card given status ID.
 * See: https://dev.twitter.com/web/embedded-tweets/parameters
 */
angular
    .module('Tweetement')
    .directive('twStatus', function () {
        return {
            restrict: 'A',
            transclude: true,
            replace: true,
            scope: {
                sid: '@'
            },
            link: function (scope, elem, attrs) {
                twttr.widgets.createTweet(
                    scope.sid,
                    elem[0],
                    {
                        cards: 'hidden',
                        conversation: 'none',
                        omit_script: true,
                        dnt: true,
                        width: 500
                    })
                    .then(function (elem) {
                        if (!elem) {
                            var e = document.getElementById('status-' + scope.sid);
                            if (e) {
                                e.style.display = 'none';
                                console.log('status ' + scope.sid + ' is not available.');
                            }
                        }
                    });
            }
        }
    });


/**
 * Base controller.
 */
angular
    .module('Tweetement')
    .controller('BaseCtrl', ['$scope', function ($scope) {
        $scope.loading = false;
        $scope.$parent.error_message = null;
    }]);


/**
 * Main view controller.
 */
angular
    .module('Tweetement')
    .controller('MainCtrl', ['$scope', '$http', '$state',
    function ($scope, $http, $state) {
        $scope.$parent.loading = false;
        $scope.$parent.error_message = null;

        $scope.enqueue = function (request) {
            $scope.$parent.loading = true;

            $http.post('/api/enqueue', request)
                .success(function (data, status) {
                    $scope.$parent.loading = false;
                    $state.go('result', {qid: data.qid});
                })
                .error(function (data, status) {
                    $scope.$parent.loading = false;
                    if (data.error_message) {
                        $scope.$parent.error_message = data.error_message;
                    }
                });
        };

        var init = function () {
            $scope.latest_loading = true;
            $http.get('/api/latest')
                .success(function (data, status) {
                    $scope.latest_loading = false;
                    $scope.latest = data;
                })
                .error(function (data, status) {
                    $scope.latest_loading = false;
                    console.log('Couldn\'t fetch latest queries.');
                });
        };

        init();
    }]);


/**
 * Results view controller.
 */
angular
    .module('Tweetement')
    .controller('ResultCtrl', ['$scope', '$http', '$stateParams', '$timeout',
    function ($scope, $http, $stateParams, $timeout) {
        $scope.$parent.loading = false;
        $scope.$parent.error_message = null;

        $scope.qid = $stateParams.qid;
        $scope.scores = {};

        var init = function () {
            getResults($scope.qid);
            getScores($scope.qid);
        };

        $scope.feedback = function (qid, sid, score) {
            $scope.scores[sid] = score;
            $http.post('/api/feedback', {qid: qid, sid: sid, score: score})
                .success(function (data, status) {
                    // Yay.
                })
                .error(function (data, status) {
                    $scope.scores[sid] = undefined;
                    if (data.error_message) {
                        $scope.$parent.error_message = data.error_message;
                    }
                });
        };

        var getResults = function (qid) {
            $scope.$parent.loading = true;

            $http.get('/api/result', {params: {qid: qid}})
                .success(function (data, status) {
                    $scope.$parent.loading = false;
                    $scope.data = data;
                    if (data.status == 'Working' || data.status == 'Pending') {
                        $timeout(function () {
                            getResults(qid);
                        }, 5000);
                    }
                })
                .error(function (data, status) {
                    $scope.$parent.loading = false;
                    if (data.error_message) {
                        $scope.$parent.error_message = data.error_message;
                    }
                });
        };

        var getScores = function (qid) {
            $http.get('/api/scores', {params: {qid: qid}})
                .success(function (data, status) {
                    angular.forEach(data['items'], function (v) {
                        $scope.scores[v.sid] = v.score;
                    });
                })
                .error(function (data, status) {
                    if (data.error_message) {
                        $scope.$parent.error_message = data.error_message;
                    }
                });
        };

        init();
    }]);