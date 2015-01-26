angular.module('Tweetement', ['ui.router'])
    .config(['$stateProvider', '$urlRouterProvider', function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise("/");

        $stateProvider
            .state('index', {
                url: "/",
                templateUrl: "assets/partials/main.html",
                controller: 'MainCtrl'
            })
            .state('result', {
                url: "/result",
                templateUrl: "assets/partials/result.html",
                controller: 'ResultCtrl'
            })
            .state('info', {
                url: "/info",
                templateUrl: "assets/partials/info.html",
                controller: 'InfoCtrl'
            });

    }]);


angular
    .module('Tweetement')
    .controller('BaseCtrl', ['$scope', function ($scope) {
    }]);


angular
    .module('Tweetement')
    .controller('MainCtrl', ['$scope', '$http', function ($scope, $http) {
        $scope.title = 'Main view';
    }]);


angular
    .module('Tweetement')
    .controller('ResultCtrl', ['$scope', '$http', function ($scope, $http) {
        $scope.title = 'Results view'
    }]);


angular
    .module('Tweetement')
    .controller('InfoCtrl', ['$scope', '$http', function ($scope, $http) {
        $scope.title = 'Information view'
    }]);
