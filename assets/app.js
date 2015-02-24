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
    }]);


/**
 * Main view controller.
 */
angular
    .module('Tweetement')
    .controller('MainCtrl', ['$scope', '$http', function ($scope, $http) {

        $scope.enqueue = function (request) {
            $scope.$parent.loading = true;
            $scope.success = null;
            $scope.error = null;
            $scope.qid = null;

            $http.post('/api/enqueue', request)
                .success(function (data, status) {
                    $scope.$parent.loading = false;
                    $scope.success = true;
                    $scope.qid = data.qid;
                })
                .error(function (data, status) {
                    $scope.$parent.loading = false;
                    $scope.error = status === 400 ?
                        data.error : 'Sorry! There was an unknown problem.';
                });
        };
    }]);


/**
 * Results view controller.
 */
angular
    .module('Tweetement')
    .controller('ResultCtrl', ['$scope', '$http', '$stateParams', '$timeout',
    function ($scope, $http, $stateParams, $timeout) {
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
                });
        };

        var getResults = function (qid) {
            $scope.$parent.loading = true;

            $http.get('/api/result', {params: {qid: qid}})
                .success(function (data, status) {
                    $scope.$parent.loading = false;
                    $scope.data = data;
                    if (data.status == 'Working') {
                        $timeout(function () {
                            getResults(qid);
                        }, 4000);
                    }
                })
                .error(function (data, status) {
                    $scope.$parent.loading = false;
                    console.log(data);
                });
        };

        var getScores = function (qid) {
            $http.get('/api/scores', {params: {qid: qid}})
                .success(function (data, status) {
                    console.log(data);
                    angular.forEach(data['items'], function (v) {
                        $scope.scores[v.sid] = v.score;
                    });
                })
                .error(function (data, status) {
                    console.log(data);
                });
        };

        init();
    }]);