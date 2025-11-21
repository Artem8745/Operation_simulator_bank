let currentAccount = null;
let userAccounts = [];

const dashboardDoc = document.querySelector('#dashboard')
const operationsDoc = document.querySelector('#operations')
const historyDoc = document.querySelector('#history')
const createAccountCardDoc = document.querySelector('#createAccountCard')

function showSection(param) {
   if (param == 'dashboard') {
      createAccountCardDoc.classList.add('hidden-display-none')
      operationsDoc.classList.add('hidden-display-none')
      historyDoc.classList.add('hidden-display-none')
      dashboardDoc.classList.remove('hidden-display-none')
   } else if (param == 'operations') {
      createAccountCardDoc.classList.add('hidden-display-none')
      dashboardDoc.classList.add('hidden-display-none')
      historyDoc.classList.add('hidden-display-none')
      operationsDoc.classList.remove('hidden-display-none')
   } else if (param == 'history') {
      createAccountCardDoc.classList.add('hidden-display-none')
      dashboardDoc.classList.add('hidden-display-none')
      operationsDoc.classList.add('hidden-display-none')
      historyDoc.classList.remove('hidden-display-none')
   } else if (param == 'createAccountCard') {
      createAccountCardDoc.classList.remove('hidden-display-none')
      dashboardDoc.classList.add('hidden-display-none')
      operationsDoc.classList.add('hidden-display-none')
      historyDoc.classList.add('hidden-display-none')
   }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
   console.log('Страница загружена');
   loadAccounts();
});

// Получение CSRF токена
function getCSRFToken() {
   const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
   if (csrfToken) {
      return csrfToken.value;
   }

   // Альтернативный способ получения CSRF токена
   const name = 'csrftoken';
   let cookieValue = null;
   if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
         const cookie = cookies[i].trim();
         if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
         }
      }
   }
   return cookieValue;
}

// Загрузка счетов пользователя
async function loadAccounts() {
   try {
      console.log('Загрузка счетов...');

      const response = await fetch('/api/accounts/my/', {
         credentials: 'include' // Важно для передачи cookies
      });

      console.log('Статус ответа:', response.status);

      if (response.status === 403) {
         showNotification('Требуется авторизация. Перенаправление на страницу входа...', 'error');
         setTimeout(() => {
            window.location.href = '/api/auth/login/';
         }, 2000);
         return;
      }

      if (!response.ok) {
         throw new Error(`HTTP error! status: ${response.status}`);
      }

      userAccounts = await response.json();
      console.log('Загружено счетов:', userAccounts.length);
      updateAccountSelects();
      showNotification('Счета загружены', 'success');

   } catch (error) {
      console.error('Ошибка загрузки счетов:', error);
      if (error.message.includes('403')) {
         showNotification('Доступ запрещен. Пожалуйста, войдите в систему.', 'error');
         setTimeout(() => {
            window.location.href = '/api/auth/login/';
         }, 3000);
      } else {
         showNotification('Ошибка загрузки счетов: ' + error.message, 'error');
      }
   }
}

// Обновление выпадающих списков счетов
function updateAccountSelects() {
   const accountSelect = document.getElementById('accountSelect');
   const operationAccountSelect = document.getElementById('operationAccountSelect');
   const historyAccountSelect = document.getElementById('historyAccountSelect');

   // Сохраняем текущее выбранное значение
   const currentSelection = accountSelect ? accountSelect.value : null;

   // Очищаем списки
   if (accountSelect) {
      accountSelect.innerHTML = '<option value="">-- Выберите счет --</option>';
   }
   if (operationAccountSelect) {
      operationAccountSelect.innerHTML = '<option value="">-- Выберите счет --</option>';
   }
   if (historyAccountSelect) {
      historyAccountSelect.innerHTML = '<option value="">-- Все счета --</option>';
   }

   // Заполняем списки
   userAccounts.forEach(account => {
      const optionText = `${account.account_number} - ${account.balance.toFixed(2)} ${account.currency}`;

      if (accountSelect) {
         const option = document.createElement('option');
         option.value = account.id;
         option.textContent = optionText;
         accountSelect.appendChild(option);
      }

      if (operationAccountSelect) {
         const option = document.createElement('option');
         option.value = account.id;
         option.textContent = optionText;
         operationAccountSelect.appendChild(option);
      }

      if (historyAccountSelect) {
         const historyOption = document.createElement('option');
         historyOption.value = account.id;
         historyOption.textContent = `${account.account_number} - ${account.client_name} (${account.currency})`;
         historyAccountSelect.appendChild(historyOption);
      }
   });

   // Восстанавливаем выбранные значения
   if (currentSelection && accountSelect) {
      accountSelect.value = currentSelection;
   }
}

// Создание нового счета
async function createNewAccount() {
   const currency = document.getElementById('newAccountCurrency').value;

   try {
      const response = await fetch('/api/accounts/create/', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
         },
         credentials: 'include',
         body: JSON.stringify({
            currency: currency
         })
      });

      const result = await response.json();

      if (response.ok && result.success) {
         showNotification(result.message, 'success');
         showSection('dashboard');
         loadAccounts();
      } else {
         showNotification(result.error, 'error');
      }
   } catch (error) {
      showNotification('Ошибка создания счета: ' + error.message, 'error');
   }
}

// Загрузка данных выбранного счета
async function loadAccountData() {
   const accountId = document.getElementById('accountSelect').value;

   if (!accountId) {
      document.getElementById('accountInfo').style.display = 'none';
      document.getElementById('quickOperations').style.display = 'none';
      currentAccount = null;
      return;
   }

   try {
      const response = await fetch(`/api/accounts/${accountId}/`, {
         credentials: 'include'
      });

      if (!response.ok) throw new Error('Ошибка загрузки данных счета');

      const accountData = await response.json();
      currentAccount = accountData;
      displayAccountInfo(accountData);
      document.getElementById('quickOperations').style.display = 'block';
      showNotification('Данные счета загружены', 'success');
   } catch (error) {
      showNotification('Ошибка загрузки данных счета: ' + error.message, 'error');
   }
}

// Отображение информации о счете
function displayAccountInfo(accountData) {
   document.getElementById('clientName').textContent = accountData.client_name;
   document.getElementById('accountNumber').textContent = accountData.account_number;
   document.getElementById('accountBalance').textContent = `${accountData.balance.toFixed(2)}`;
   document.getElementById('accountCurrency').textContent = accountData.currency;
   document.getElementById('accountCreated').textContent = new Date(accountData.created_at).toLocaleDateString();
   document.getElementById('accountInfo').style.display = 'block';
}

// Поиск счетов для перевода
async function searchAccounts() {
   const query = document.getElementById('toAccountNumber').value;

   if (query.length < 4) {
      showNotification('Введите минимум 4 символа для поиска', 'error');
      return;
   }

   try {
      const response = await fetch(`/api/accounts/search/?q=${encodeURIComponent(query)}`, {
         credentials: 'include'
      });

      if (!response.ok) throw new Error('Ошибка поиска');

      const results = await response.json();
      displaySearchResults(results);
   } catch (error) {
      showNotification('Ошибка поиска: ' + error.message, 'error');
   }
}

function displaySearchResults(results) {
   const container = document.getElementById('searchResults');

   if (results.error) {
      container.innerHTML = `${results.error}</div>`;
      return;
   }

   if (results.length === 0) {
      container.innerHTML = '<div style="color: #666;">Счета не найдены</div>';
      return;
   }

   container.innerHTML = results.map(account => `
        <div class="search-result" onclick="selectAccount('${account.account_number}', '${account.client_name}')"
            <strong>${account.account_number}</strong> - ${account.client_name}
        </div>
    `).join('');
}

function selectAccount(accountNumber, clientName) {
   document.getElementById('toAccountNumber').value = accountNumber;
   document.getElementById('searchResults').innerHTML = `<div style="color: var(--color-accent);">Выбран: ${clientName}</div>`;
}

// Операция пополнения
async function deposit() {
   const accountId = document.getElementById('operationAccountSelect').value;
   const amount = parseFloat(document.getElementById('depositAmount').value);
   const description = document.getElementById('depositDescription').value || 'Пополнение счета';

   if (!accountId) {
      showNotification('Выберите счет для операции', 'error');
      return;
   }

   if (!amount || amount <= 0) {
      showNotification('Введите корректную сумму', 'error');
      return;
   }

   try {
      const response = await fetch('/api/deposit/', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
         },
         credentials: 'include',
         body: JSON.stringify({
            account_id: parseInt(accountId),
            amount: amount,
            description: description
         })
      });

      const result = await response.json();

      if (response.ok && result.success) {
         showNotification(result.message, 'success');
         document.getElementById('depositAmount').value = '';
         document.getElementById('depositDescription').value = '';
         loadAccounts();
         if (currentAccount && currentAccount.id === parseInt(accountId)) {
            loadAccountData();
         }
      } else {
         showNotification(result.error, 'error');
      }
   } catch (error) {
      showNotification('Ошибка операции: ' + error.message, 'error');
   }
}

// Операция снятия
async function withdraw() {
   const accountId = document.getElementById('operationAccountSelect').value;
   const amount = parseFloat(document.getElementById('withdrawAmount').value);
   const description = document.getElementById('withdrawDescription').value || 'Снятие наличных';

   if (!accountId) {
      showNotification('Выберите счет для операции', 'error');
      return;
   }

   if (!amount || amount <= 0) {
      showNotification('Введите корректную сумму', 'error');
      return;
   }

   try {
      const response = await fetch('/api/withdraw/', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
         },
         credentials: 'include',
         body: JSON.stringify({
            account_id: parseInt(accountId),
            amount: amount,
            description: description
         })
      });

      const result = await response.json();

      if (response.ok && result.success) {
         showNotification(result.message, 'success');
         document.getElementById('withdrawAmount').value = '';
         document.getElementById('withdrawDescription').value = '';
         loadAccounts();
         if (currentAccount && currentAccount.id === parseInt(accountId)) {
            loadAccountData();
         }
      } else {
         showNotification(result.error, 'error');
      }
   } catch (error) {
      showNotification('Ошибка операции: ' + error.message, 'error');
   }
}

// Операция перевода
async function transfer() {
   const fromAccountId = document.getElementById('operationAccountSelect').value;
   const toAccountNumber = document.getElementById('toAccountNumber').value;
   const amount = parseFloat(document.getElementById('transferAmount').value);
   const description = document.getElementById('transferDescription').value || 'Перевод средств';

   if (!fromAccountId) {
      showNotification('Выберите счет для операции', 'error');
      return;
   }

   if (!toAccountNumber) {
      showNotification('Введите номер счета получателя', 'error');
      return;
   }

   if (!amount || amount <= 0) {
      showNotification('Введите корректную сумму', 'error');
      return;
   }

   try {
      const response = await fetch('/api/transfer/', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
         },
         credentials: 'include',
         body: JSON.stringify({
            from_account_id: parseInt(fromAccountId),
            to_account_number: toAccountNumber,
            amount: amount,
            description: description
         })
      });

      const result = await response.json();

      if (response.ok && result.success) {
         let message = result.message;
         if (result.exchange_rate && result.exchange_rate !== 1) {
            message += ` Конвертировано: ${result.converted_amount.toFixed(2)}`;
         }
         showNotification(message, 'success');
         document.getElementById('transferAmount').value = '';
         document.getElementById('transferDescription').value = '';
         document.getElementById('toAccountNumber').value = '';
         document.getElementById('searchResults').innerHTML = '';
         loadAccounts();
         if (currentAccount && currentAccount.id === parseInt(fromAccountId)) {
            loadAccountData();
         }
      } else {
         showNotification(result.error, 'error');
      }
   } catch (error) {
      showNotification('Ошибка операции: ' + error.message, 'error');
   }
}

// Загрузка истории операций
async function loadAccountHistory() {
   const accountId = document.getElementById('historyAccountSelect').value;

   try {
      let url = '/api/accounts/my/';
      if (accountId) {
         url = `/api/accounts/${accountId}/`;
      }

      const response = await fetch(url, {
         credentials: 'include'
      });

      if (!response.ok) throw new Error('Ошибка загрузки истории');

      const data = await response.json();

      if (accountId) {
         displayTransactions(data.transactions || []);
      } else {
         const allTransactions = [];
         if (Array.isArray(data)) {
            for (const account of data) {
               const accountResponse = await fetch(`/api/accounts/${account.id}/`, {
                  credentials: 'include'
               });
               if (accountResponse.ok) {
                  const accountData = await accountResponse.json();
                  allTransactions.push(...(accountData.transactions || []));
               }
            }
         }
         allTransactions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
         displayTransactions(allTransactions.slice(0, 50));
      }

   } catch (error) {
      showNotification('Ошибка загрузки истории: ' + error.message, 'error');
   }
}

// Отображение списка транзакций с правильными валютами
function displayTransactions(transactions) {
   const transactionList = document.getElementById('transactionHistory');

   if (!transactions || transactions.length === 0) {
      transactionList.innerHTML = '<p>Нет операций</p>';
      return;
   }

   transactionList.innerHTML = transactions.map(transaction => {
      // Используем валюту из данных транзакции
      const displayCurrency = transaction.currency || 'RUB';
      const amount = transaction.amount;

      // Определяем знак и класс для стилизации
      let sign = '';
      let amountClass = '';

      if (transaction.type === 'deposit') {
         sign = '+';
         amountClass = 'positive';
      } else if (transaction.type === 'withdraw') {
         sign = '-';
         amountClass = 'negative';
      } else if (transaction.type === 'transfer') {
         // Для переводов определяем направление по стрелкам в описании
         if (transaction.description && transaction.description.includes('←')) {
            // Входящий перевод
            sign = '+';
            amountClass = 'positive';
         } else {
            // Исходящий перевод
            sign = '-';
            amountClass = 'negative';
         }
      }

      // Форматируем дату
      const transactionDate = new Date(transaction.timestamp);
      const formattedDate = transactionDate.toLocaleDateString('ru-RU') + ' ' + transactionDate.toLocaleTimeString('ru-RU', {
         hour: '2-digit',
         minute: '2-digit'
      });

      return `
        <div class="transaction-item">
            <div class="transaction-header">
                <span class="transaction-type">${transaction.type_display || transaction.type}</span>
                <span class="transaction-amount ${amountClass}">
                    ${sign}${amount.toFixed(2)} ${displayCurrency}
                </span>
            </div>
            <div class="transaction-description">${transaction.description}</div>
            <div class="transaction-meta">
                <span class="transaction-date">${formattedDate}</span>
                ${transaction.from_account ? `<span class="transaction-account">→ ${transaction.to_account || ''}</span>` : ''}
            </div>
        </div>
        `;
   }).join('');
}

// Переключение между разделами
function showSection(sectionName) {
   document.querySelectorAll('.section').forEach(section => {
      section.style.display = 'none';
   });

   document.getElementById(sectionName).style.display = 'block';
}

// Показать уведомление
function showNotification(message, type = 'success') {
   const notification = document.getElementById('notification');
   if (notification) {
      notification.textContent = message;
      notification.className = `notification ${type}`;
      notification.classList.remove('hidden');

      setTimeout(() => {
         notification.classList.add('hidden');
      }, 5000);
   } else {
      // Fallback: использовать alert если элемент notification не найден
      alert(`${type.toUpperCase()}: ${message}`);
   }
}