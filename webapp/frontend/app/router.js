import Ember from 'ember';
import config from './config/environment';

var Router = Ember.Router.extend({
  location: config.locationType,
});

Router.map(function() {

  this.resource('user', function() {
		// /user/login
		this.route('login');
  		// /user/logout
  		this.route('logout');
    // /user/clusters
    this.route('clusters');
	});
  this.route('create-lambda-instance');
});

export default Router;
