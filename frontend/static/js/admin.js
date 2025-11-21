let currentDisplayLimit = 10;
let currentLoadLimit = 10;
let allTransactions = [];
let isLoading = false;
let searchTimeout = null;
let hasMoreData = true;

// Функция для синхронизации select с текущим лимитом
function syncLimitSelect() {
   const limitSelect = document.getElementById('transactionsLimit');
   if (!limitSelect) return;

   const currentValueStr = currentLoadLimit.toString();

   // Проверяем, есть ли такое значение в select
   for (let option of limitSelect.options) {
      if (option.value === currentValueStr) {
         // Если нашли совпадение - выбираем этот пункт
         limitSelect.value = currentValueStr;
         return;
      }
   }

   // Если не нашли совпадение - оставляем select как есть
}

// Функция для загрузки последних транзакций
async function loadRecentTransactions() {
   if (isLoading) return;

   try {
      isLoading = true;

      // Берем начальное значение из select только при первой загрузке
      const limitSelect = document.getElementById('transactionsLimit');
      if (limitSelect) {
         currentLoadLimit = parseInt(limitSelect.value) || 10;
      }

      showLoadingState(true);

      const searchTerm = document.getElementById('transactionSearch').value.trim();
      const filterType = document.getElementById('filterType').value;

      if (searchTerm) {
         await searchTransactions();
         return;
      }

      const response = await fetch(`/api/admin/recent-transactions/?limit=${currentLoadLimit}`);
      if (!response.ok) throw new Error('Ошибка загрузки транзакций');

      const data = await response.json();
      allTransactions = data.transactions || [];
      currentDisplayLimit = allTransactions.length;

      hasMoreData = true;
      displayRecentTransactions(allTransactions);
      updateTransactionsInfo(data);
      updateLoadMoreButton(data);

      // Синхронизируем select после загрузки
      syncLimitSelect();

   } catch (error) {
      console.error('Ошибка:', error);
      document.getElementById('recentTransactionsContainer').innerHTML =
         '<p>Ошибка загрузки транзакций: ' + error.message + '</p>';
   } finally {
      isLoading = false;
      showLoadingState(false);
   }
}

// Функция для загрузки дополнительных транзакций
async function loadMoreTransactions() {
   if (isLoading) return;

   try {
      isLoading = true;
      showLoadingState(true);

      // Увеличиваем наш внутренний лимит на 10
      const newLoadLimit = currentLoadLimit + 10;

      // Проверяем максимальный лимит
      if (newLoadLimit > 4000) {
         alert('Максимальное количество транзакций для отображения: 4000');
         document.getElementById('loadMoreContainer').style.display = 'none';
         return;
      }

      // Обновляем нашу переменную
      currentLoadLimit = newLoadLimit;

      const searchTerm = document.getElementById('transactionSearch').value.trim();
      if (searchTerm) {
         await performSearchWithLimit(searchTerm, newLoadLimit);
      } else {
         await performLoadWithLimit(newLoadLimit);
      }

      // Синхронизируем select после загрузки
      syncLimitSelect();

   } catch (error) {
      console.error('Ошибка загрузки дополнительных транзакций:', error);
      alert('Ошибка загрузки дополнительных транзакций: ' + error.message);
   } finally {
      isLoading = false;
      showLoadingState(false);
   }
}

// Вспомогательная функция для загрузки с указанным лимитом
async function performLoadWithLimit(limit) {
   try {
      const response = await fetch(`/api/admin/recent-transactions/?limit=${limit}`);
      if (!response.ok) throw new Error('Ошибка загрузки транзакций');

      const data = await response.json();
      const newTransactions = data.transactions || [];

      // Если пришел пустой массив или меньше транзакций чем лимит - значит больше данных нет
      if (newTransactions.length === 0 || newTransactions.length < limit) {
         hasMoreData = false;
      }

      allTransactions = newTransactions;
      currentDisplayLimit = allTransactions.length;
      currentLoadLimit = limit;

      displayRecentTransactions(allTransactions);
      updateTransactionsInfo(data);
      updateLoadMoreButton(data);

   } catch (error) {
      console.error('Ошибка при загрузке транзакций:', error);
      document.getElementById('recentTransactionsContainer').innerHTML =
         '<p>Ошибка загрузки транзакций: ' + error.message + '</p>';
      throw error;
   }
}

// Вспомогательная функция для поиска с указанным лимитом
async function performSearchWithLimit(searchTerm, limit) {
   try {
      const filterType = document.getElementById('filterType').value;

      const params = new URLSearchParams({
         q: searchTerm,
         limit: limit
      });

      if (filterType && filterType !== 'all') {
         params.append('type', filterType);
      }

      const response = await fetch(`/api/admin/search-transactions/?${params}`);

      if (!response.ok) {
         const errorText = await response.text();
         throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();

      if (data.error) {
         throw new Error(data.error);
      }

      const newTransactions = data.transactions || [];

      // Если пришел пустой массив или меньше транзакций чем лимит - значит больше данных нет
      if (newTransactions.length === 0 || newTransactions.length < limit) {
         hasMoreData = false;
      }

      allTransactions = newTransactions;
      currentDisplayLimit = allTransactions.length;
      currentLoadLimit = limit;

      displayRecentTransactions(allTransactions);
      updateTransactionsInfo(data);
      updateLoadMoreButton(data);

      // Обновляем информацию о поиске
      const infoElement = document.getElementById('loadedTransactionsInfo');
      if (infoElement) {
         const foundText = data.total_count === 0 ?
            'Транзакции не найдены' :
            `Найдено: ${data.total_count} транзакций`;
         const limitInfo = data.limit ? ` (лимит: ${data.limit})` : '';
         infoElement.innerHTML =
            `<strong>${foundText}${limitInfo}</strong> по запросу "${searchTerm}"`;
      }

   } catch (error) {
      console.error('Ошибка при поиске транзакций:', error);
      const container = document.getElementById('recentTransactionsContainer');
      if (container) {
         container.innerHTML =
            `<div>
               <h3>Ошибка поиска</h3>
               <p>${error.message}</p>
               <button onclick="resetFilters()">
                     Сбросить фильтры
               </button>
            </div>`;
      }
      throw error;
   }
}

// Функция для отображения состояния загрузки
function showLoadingState(loading) {
   const container = document.getElementById('recentTransactionsContainer');
   const loadMoreBtn = document.querySelector('#loadMoreContainer button');

   if (loading) {
      // Не показываем спиннер если уже отображаются транзакции
      if (container && allTransactions.length === 0) {
         container.innerHTML = '<div><div class="loading-spinner"></div><p>Загрузка...</p></div>';
      }
      if (loadMoreBtn) {
         loadMoreBtn.disabled = true;
         loadMoreBtn.innerHTML = 'Загрузка...';
      }
   } else {
      if (loadMoreBtn) {
         loadMoreBtn.disabled = false;
         loadMoreBtn.innerHTML = 'Показать еще транзакции';
      }
   }
}

// Функция для отображения последних транзакций
function displayRecentTransactions(transactions) {
   const container = document.getElementById('recentTransactionsContainer');
   if (!container) return;

   if (!transactions || transactions.length === 0) {
      container.innerHTML = '<p>Нет транзакций для отображения</p>';
      return;
   }

   container.innerHTML = transactions.map((transaction, index) => {
      // Определяем знак и класс для стилизации
      let sign = '';
      let amountClass = '';

      if (transaction.type === 'Пополнение' || transaction.type.toLowerCase() === 'deposit') {
         sign = '+';
         amountClass = 'deposit';
      } else if (transaction.type === 'Снятие' || transaction.type.toLowerCase() === 'withdraw') {
         sign = '-';
         amountClass = 'withdraw';
      } else if (transaction.type === 'Перевод' || transaction.type.toLowerCase() === 'transfer') {
         // Для переводов определяем направление по стрелкам в описании
         if (transaction.description && transaction.description.includes('←')) {
            // Входящий перевод
            sign = '+';
            amountClass = 'deposit';
         } else {
            // Исходящий перевод
            sign = '-';
            amountClass = 'withdraw';
         }
      }

      // Форматируем дату
      const transactionDate = new Date(transaction.timestamp);
      const formattedDate = transactionDate.toLocaleDateString('ru-RU') + ' ' +
         transactionDate.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
         });

      // Определяем информацию о переводе
      let transferInfo = '';
      if (transaction.type === 'Перевод' && transaction.from_account && transaction.to_account) {
         if (transaction.description && transaction.description.includes('←')) {
            transferInfo = `← ${transaction.from_account}`;
         } else {
            transferInfo = `→ ${transaction.to_account}`;
         }
      }

      return `
            <div class="transaction-item" data-index="${index}">
                <div class="transaction-header">
                    <div>
                        <strong>${transaction.client_name}</strong>
                        <div>
                            ${transaction.account_number}
                            ${transaction.currency ? `(${transaction.currency})` : ''}
                        </div>
                    </div>
                    <span class="transaction-amount ${amountClass}">
                        ${sign}${transaction.amount.toFixed(2)} ${transaction.currency}
                    </span>
                </div>
                <div class="transaction-description">
                    ${transaction.description}
                </div>
                <div class="transaction-meta">
                    <span class="transaction-date">${formattedDate}</span>
                    ${transferInfo ? `<span class="transfer-direction">${transferInfo}</span>` : ''}
                </div>
            </div>
            `;
   }).join('');
}

// Обновление информации о загруженных транзакциях
function updateTransactionsInfo(data) {
   const infoElement = document.getElementById('loadedTransactionsInfo');
   if (infoElement && data) {
      const loadedCount = data.transactions ? data.transactions.length : 0;
      infoElement.innerHTML = `<strong>Загружено:</strong> ${loadedCount} транзакций (лимит: ${currentLoadLimit})`;
   }
}

// Управление кнопкой "Показать еще"
function updateLoadMoreButton(data) {
   const loadMoreContainer = document.getElementById('loadMoreContainer');
   if (!loadMoreContainer) return;

   const currentLimit = parseInt(document.getElementById('transactionsLimit').value);

   // Определяем есть ли еще данные для загрузки
   let shouldShowButton = true;

   // Если достигнут максимальный лимит - скрываем кнопку
   if (currentLimit >= 4000) {
      shouldShowButton = false;
   }
   // Если сервер вернул информацию о наличии данных - используем ее
   else if (data && data.has_more !== undefined) {
      shouldShowButton = data.has_more;
   }
   // Иначе используем логику: если загружено меньше транзакций чем лимит - значит больше данных нет
   else if (allTransactions.length < currentLimit) {
      shouldShowButton = false;
   }
   // Используем глобальный флаг как запасной вариант
   else if (!hasMoreData) {
      shouldShowButton = false;
   }

   loadMoreContainer.style.display = shouldShowButton ? 'block' : 'none';
}

// Функция для поиска с задержкой
function handleSearchInput() {
   clearTimeout(searchTimeout);
   searchTimeout = setTimeout(() => {
      const searchTerm = document.getElementById('transactionSearch').value.trim();
      if (searchTerm) {
         searchTransactions();
      } else {
         // При очистке поиска сбрасываем лимит и загружаем заново
         document.getElementById('transactionsLimit').value = '10';
         loadRecentTransactions();
      }
   }, 500);
}

// Поиск транзакций с запросом к серверу
async function searchTransactions() {
   if (isLoading) return;

   try {
      isLoading = true;
      showLoadingState(true);

      const searchTerm = document.getElementById('transactionSearch').value.trim();
      const filterType = document.getElementById('filterType').value;
      const selectedLimit = document.getElementById('transactionsLimit').value;

      // Если поисковый запрос пустой, загружаем обычные транзакции
      if (!searchTerm) {
         await loadRecentTransactions();
         return;
      }

      // Сбрасываем флаг наличия данных при новом поиске
      hasMoreData = true;

      // Собираем параметры запроса
      const params = new URLSearchParams({
         q: searchTerm,
         limit: selectedLimit
      });

      if (filterType && filterType !== 'all') {
         params.append('type', filterType);
      }

      const response = await fetch(`/api/admin/search-transactions/?${params}`);

      if (!response.ok) {
         const errorText = await response.text();
         throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();

      // Проверяем наличие ошибки в ответе
      if (data.error) {
         throw new Error(data.error);
      }

      allTransactions = data.transactions || [];
      currentDisplayLimit = allTransactions.length;
      currentLoadLimit = parseInt(selectedLimit);

      displayRecentTransactions(allTransactions);
      updateTransactionsInfo(data);
      updateLoadMoreButton(data);

      // Обновляем информацию о поиске
      const infoElement = document.getElementById('loadedTransactionsInfo');
      if (infoElement) {
         const foundText = data.total_count === 0 ?
            'Транзакции не найдены' :
            `Найдено: ${data.total_count} транзакций`;
         const limitInfo = data.limit ? ` (лимит: ${data.limit})` : '';
         infoElement.innerHTML =
            `<strong>${foundText}${limitInfo}</strong> по запросу "${searchTerm}"`;
      }

      // Синхронизируем select после поиска
      syncLimitSelect();

   } catch (error) {
      console.error('Ошибка поиска:', error);
      const container = document.getElementById('recentTransactionsContainer');
      if (container) {
         container.innerHTML =
            `<div>
               <h3>Ошибка поиска</h3>
               <p>${error.message}</p>
               <button onclick="resetFilters()">
                  Сбросить фильтры
               </button>
            </div>`;
      }
   } finally {
      isLoading = false;
      showLoadingState(false);
   }
}

// Фильтрация транзакций по типу
async function filterTransactions(type) {
   const searchTerm = document.getElementById('transactionSearch').value.trim();
   const selectedLimit = document.getElementById('transactionsLimit').value;

   // Если есть поисковый запрос, выполняем поиск с фильтром
   if (searchTerm) {
      await searchTransactions();
   } else {
      // Иначе фильтруем локально
      let filteredTransactions = allTransactions;

      if (type !== 'all') {
         filteredTransactions = allTransactions.filter(transaction => {
            const transactionType = transaction.type.toLowerCase();
            if (type === 'deposit') return transactionType.includes('пополнение') || transactionType === 'deposit';
            if (type === 'withdraw') return transactionType.includes('снятие') || transactionType === 'withdraw';
            if (type === 'transfer') return transactionType.includes('перевод') || transactionType === 'transfer';
            return true;
         });
      }

      // Применяем лимит
      if (selectedLimit && filteredTransactions.length > selectedLimit) {
         filteredTransactions = filteredTransactions.slice(0, selectedLimit);
      }

      displayRecentTransactions(filteredTransactions);

      // Обновляем информацию
      const infoElement = document.getElementById('loadedTransactionsInfo');
      if (infoElement) {
         infoElement.innerHTML = `<strong>Отфильтровано:</strong> ${filteredTransactions.length} транзакций (лимит: ${selectedLimit})`;
      }

      // При фильтрации скрываем кнопку "Показать еще"
      document.getElementById('loadMoreContainer').style.display = 'none';
   }
}

// Обработчик изменения лимита в select
function handleLimitChange() {
   const limitSelect = document.getElementById('transactionsLimit');
   if (limitSelect) {
      // Обновляем наш внутренний лимит из select
      currentLoadLimit = parseInt(limitSelect.value) || 10;
   }

   const searchTerm = document.getElementById('transactionSearch').value.trim();
   if (searchTerm) {
      searchTransactions();
   } else {
      loadRecentTransactions();
   }
}

// Сброс фильтров и поиска
async function resetFilters() {
   document.getElementById('transactionSearch').value = '';
   document.getElementById('filterType').value = 'all';

   // Сбрасываем select к начальному значению
   const limitSelect = document.getElementById('transactionsLimit');
   if (limitSelect) {
      limitSelect.value = '10';
   }

   // Сбрасываем наш внутренний лимит
   currentLoadLimit = 10;
   hasMoreData = true;

   await loadRecentTransactions();
}

// Функция для тестирования API
async function testAdminAPI() {
   try {
      const response = await fetch('/api/admin/check/');
      const data = await response.json();
      alert(`API работает! Пользователь: ${data.user}`);
   } catch (error) {
      alert('Ошибка API: ' + error.message);
   }
}

// Функция для загрузки всех данных
async function loadAdminData() {
   await loadRecentTransactions();
}

// admin.js - скрипт для админ-панели
class AdminPanel {
   constructor() {
      this.init();
   }

   init() {
      this.setupEventListeners();
      this.loadAdminData();
   }

   setupEventListeners() {
      // Обработчики для кнопок админ-панели
      const refreshBtn = document.querySelector('button[onclick="loadAdminData()"]');
      if (refreshBtn) {
         refreshBtn.addEventListener('click', () => this.loadAdminData());
      }

      const testBtn = document.querySelector('button[onclick="testAdminAPI()"]');
      if (testBtn) {
         testBtn.addEventListener('click', () => this.testAdminAPI());
      }
   }

   async loadAdminData() {
      try {
         // Устанавливаем начальный лимит
         const limitSelect = document.getElementById('transactionsLimit');
         if (limitSelect) {
            limitSelect.value = '10';
            currentLoadLimit = 10;
         }

         await Promise.all([
            this.loadTransactions(),
            this.loadStats()
         ]);
      } catch (error) {
         console.error('Ошибка загрузки данных:', error);
      }
   }

   async loadTransactions() {
      try {
         // Загружаем с текущим лимитом (10)
         const response = await fetch(`/api/admin/recent-transactions/?limit=${currentLoadLimit}`);
         if (!response.ok) throw new Error('Ошибка загрузки транзакций');

         const data = await response.json();
         allTransactions = data.transactions || [];
         currentDisplayLimit = allTransactions.length;

         this.displayTransactions(allTransactions);
         updateTransactionsInfo(data);
         updateLoadMoreButton(data);

         // Синхронизируем select
         syncLimitSelect();

      } catch (error) {
         console.error('Ошибка загрузки транзакций:', error);
      }
   }

   async loadStats() {
      try {
         const response = await fetch('/api/admin/accounts/');
         if (!response.ok) throw new Error('Ошибка загрузки статистики');

         const accounts = await response.json();
         this.updateStats(accounts);
      } catch (error) {
         console.error('Ошибка загрузки статистики:', error);
      }
   }

   displayTransactions(transactions) {
      const container = document.getElementById('recentTransactionsContainer');
      if (!container) return;

      if (!transactions || transactions.length === 0) {
         container.innerHTML = '<p>Нет транзакций для отображения</p>';
         return;
      }

      container.innerHTML = transactions.map(transaction => {
         const amountClass = this.getAmountClass(transaction);
         const sign = this.getAmountSign(transaction);
         const formattedDate = this.formatDate(transaction.timestamp);

         return `
            <div class="transaction-item">
                <div>
                    <div>
                        <strong>${transaction.client_name}</strong>
                        <br>
                        <small>${transaction.account_number}</small>
                    </div>
                    <span class="${amountClass}">
                        ${sign}${transaction.amount.toFixed(2)} ${transaction.currency}
                    </span>
                </div>
                <div>
                    ${transaction.description}
                </div>
                <div>
                    ${formattedDate}
                    ${transaction.from_account ? `→ ${transaction.to_account}` : ''}
                </div>
            </div>
            `;
      }).join('');
   }

   getAmountClass(transaction) {
      const type = transaction.type.toLowerCase();
      if (type.includes('пополнение') || type === 'deposit') return 'deposit';
      if (type.includes('снятие') || type === 'withdraw') return 'withdraw';
      if (type.includes('перевод') || type === 'transfer') {
         return transaction.description && transaction.description.includes('←') ? 'deposit' : 'withdraw';
      }
      return '';
   }

   getAmountSign(transaction) {
      const type = transaction.type.toLowerCase();
      if (type.includes('пополнение') || type === 'deposit') return '+';
      if (type.includes('снятие') || type === 'withdraw') return '-';
      if (type.includes('перевод') || type === 'transfer') {
         return transaction.description && transaction.description.includes('←') ? '+' : '-';
      }
      return '';
   }

   formatDate(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleDateString('ru-RU') + ' ' +
         date.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
         });
   }

   updateStats(accounts) {
      // Можно добавить обновление статистики, если нужно
      console.log('Загружено счетов:', accounts.length);
   }

   async testAdminAPI() {
      try {
         const response = await fetch('/api/admin/check/');
         const data = await response.json();
         alert(`API работает! Пользователь: ${data.user}`);
      } catch (error) {
         alert('Ошибка API: ' + error.message);
      }
   }
}

// Загружаем последние транзакции при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
   // Инициализируем панель - она сама установит лимит 10
   new AdminPanel();
});