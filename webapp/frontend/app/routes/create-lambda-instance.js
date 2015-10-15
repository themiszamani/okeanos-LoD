import Ember from "ember";

export default Ember.Route.extend({
  model() {
    return Ember.RSVP.hash({
      newLambdaInstance: this.store.createRecord('create-lambda-instance', {}),
      userPublicKeys: this.store.findAll('user-public-key')
    });
  }
});
