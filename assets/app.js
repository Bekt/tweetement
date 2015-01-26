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
                url: "/result/{rid:\\d+}",
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

        $scope.enqueue = function (request) {
            $scope.success = null;
            $scope.error = null;
            $scope.rid = null;
            $http.post('/api/enqueue', request)
                .success(function (data, status) {
                    $scope.success = true;
                    $scope.rid = data.id;
                })
                .error(function (data, status) {
                    $scope.error = status === 400 ?
                        data.error : 'Sorry! There was an unknown problem.';
                });
        };
    }]);


angular
    .module('Tweetement')
    .controller('ResultCtrl', ['$scope', '$http', '$stateParams', function ($scope, $http, $stateParams) {
        $scope.title = 'Results view';
        $scope.rid = $stateParams.rid;

        var init = function (rid) {
            $http.get('/api/result', {params: {rid: rid}})
                .success(function (data, status) {
                    $scope.data = data;
                })
                .error(function (data, status) {
                    console.log('Could not load');
                    console.log(data);
                });
        };

        init($scope.rid);
    }]);


angular
    .module('Tweetement')
    .controller('InfoCtrl', ['$scope', '$http', function ($scope, $http) {
        $scope.title = 'Information view';
    }]);
