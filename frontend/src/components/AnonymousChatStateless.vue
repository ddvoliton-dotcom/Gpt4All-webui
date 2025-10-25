<template>
  <div>
    <h1>Анонимный чат (Stateless)</h1>
    <textarea v-model="message" placeholder="Ваше сообщение..."></textarea>
    <button @click="sendMessage">Отправить</button>
    <div v-if="response">
      <h2>Ответ:</h2>
      <p>{{ response }}</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      message: '',
      response: null,
    };
  },
  methods: {
    async sendMessage() {
      const res = await fetch('/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: this.message }),
      });
      this.response = await res.json();
    },
  },
};
</script>
