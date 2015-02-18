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
                        dnt: true,
                        width: 500
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
    .controller('ResultCtrl', ['$scope', '$http', '$stateParams',
    function ($scope, $http, $stateParams) {
        $scope.qid = $stateParams.qid;

        var init = function (qid) {
            $scope.$parent.loading = true;

            $http.get('/api/result', {params: {qid: qid}})
                .success(function (data, status) {
                    $scope.$parent.loading = false;
                    $scope.data = data;
                })
                .error(function (data, status) {
                    $scope.$parent.loading = false;
                    console.log(data);
                });
        };

        init($scope.qid);
    }]);