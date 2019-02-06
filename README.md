# receipt
Кривоватая библиотека для получения информации из чека по QR коду с последнего

Принимает на вход строку вида 
<code>t=20190204T214700&s=2742.00&fn=8712000101105958&i=3299&fp=1014611131&n=1</code>

Возвращает либо словарь с перечнем покупок, либо список с отфильтрованными данными (WIP). 

Для работы необходима регистрация на сайте налоговой (не учётка с личным кабинетом, а аккаунт разработчика или что-то такое). Для этого есть функция <code>registration()</code>. 

После необходимо залогиниться с помощью <code>login()</code>.
