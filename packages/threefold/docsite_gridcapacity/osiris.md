# osiris


see https://osiris-ui.github.io/osiris/#/input

learn from 

- https://github.com/osiris-ui/osiris/blob/master/docs/index.html

<template>
  <o-form
    ref="form"
    :rules="rules"
    :model="form"
    @submit="validate">

    <o-form-item
      label="Name"
      prop="name">
      <o-input v-model="form.name"></o-input>
    </o-form-item>

    <o-form-item
      label="E-mail"
      prop="email">
      <o-input v-model="form.email"></o-input>
    </o-form-item>

    <o-form-item
      label="Are your a real person?"
      prop="isReal">
      <o-radio v-model="form.isReal" :value="true">Yes</o-radio>
      <o-radio v-model="form.isReal" :value="false">No</o-radio>
    </o-form-item>

    <o-form-item
      label="Which following languages do you know?"
      prop="languages">
      <o-checkbox v-model="form.languages" value="Javascript">Javascript</o-checkbox>
      <o-checkbox v-model="form.languages" value="PHP">PHP</o-checkbox>
      <o-checkbox v-model="form.languages" value="Python">Python</o-checkbox>
      <o-checkbox v-model="form.languages" value="Ruby">Ruby</o-checkbox>
    </o-form-item>

    <o-button type="primary" native-type="submit" @click="validate">Validate</o-button>
    <o-button @click="clearValidation">Clear validation</o-button>
  </o-form>
</template>

<script>
  export default {
    data() {
      return {
        form: {
          name: '',
          email: '',
          isReal: '',
          languages: [],
        },

        rules: {
          name: {
            presence: {
              allowEmpty: false,
              message: 'Please, tell us your name',
            },
            trigger: 'blur',
          },

          email: {
            email: {
              message: 'This is not a valid email',
            },
            trigger: 'blur',
          },

          isReal: {
            presence: {
              message: 'Are you really a real person?',
            },

            validator(value) {
              if (value !== true) return 'You must be a real person';

              return undefined;
            },

            trigger: 'change',
          },

          languages: {
            presence: {
              allowEmpty: false,
              message: 'Please, select a least one',
            },

            trigger: 'change',
          },
        },
      };
    },

    methods: {
      validate() {
        return this.$refs.form.validate();
      },

      clearValidation() {
        return this.$refs.form.clearValidation();
      },
    },
  }
</script>
