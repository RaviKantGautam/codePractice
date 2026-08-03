### Customers With Positive Revenue

select customer_id from customers where year = 2020 group by customer_id having sum(revenue) > 0;

### Customers Without Orders

select name from customers where id not in (select customer_id from orders);

select c.name from customers left join orders as ord on c.customer_id = ord.customer_id where ord.customer_id is null;


### Calculate Special Bonus

select employee_id, 
case
    when employee_id % 2 != 0 and name not like 'M%' then salary
    else 0
end as bonus
from employees order by employee_id ASC;


### Customers Who Bought A and B but Not C

SELECT c.customer_id, c.customer_name
FROM customers c
WHERE c.customer_id IN (
    SELECT customer_id FROM orders WHERE product_name = 'A'
)
AND c.customer_id IN (
    SELECT customer_id FROM orders WHERE product_name = 'B'
)
AND c.customer_id NOT IN (
    SELECT customer_id FROM orders WHERE product_name = 'C'
)
ORDER BY c.customer_name;



### Combine Two Tables

SELECT pp.first_name, pp.last_name, addr.city, addr.state from person as pp left join address as addr
on pp.person_id = addr.person_id;


### Sellers With No Sales

1.
select seller_name from seller where seller_id not in (
    select distinct seller_id from orders where extract(year from sale_date) = 2020
) order by seller_name asc;

2.
SELECT s.seller_name
FROM seller AS s
LEFT JOIN orders AS o
    ON s.seller_id = o.seller_id
    AND EXTRACT(YEAR FROM o.sale_date) = 2020
WHERE o.seller_id IS NULL
ORDER BY s.seller_name ASC;


### Top Travellers

select users.name, COALESCE(sum(rides.distance), 0) as travelled_distance from users left join rides on users.id = rides.user_id
group by rides.user_id, users.name 
order by travelled_distance DESC, users.name ASC;

### Sales Person

select sp.name from sales_person as sp where sp.sales_id not in (
    select ord.sales_id from orders as ord
    inner join company as cp on ord.com_id = cp.com_id
    where cp.name = 'CRIMSON'
)


### Write a SQL query to get the second highest salary from the Employee table.

select max(salary) as sec_max_salary from employee where salary < (
    select max(salary) from employee
)


### Write a SQL query to get the second lowest salary from the Employee table.

select min(salary) as sec_max_salary from employee where salary > (
    select min(salary) from employee
)


### Write a SQL query to find all duplicate emails in a table named Person.

select email from Person group by email having count(*) > 1;


### Write a SQL query to delete all duplicate email entries in a table named Person, keeping only unique emails based on its smallest Id.

delete p1 from Person p1 join Person p2 on p1.email = p2.email and p1.id > p2.id;


### https://leetcode.com/problems/employees-earning-more-than-their-managers/

select * from Employee as emp join Employee as mng on emp.managerId = mng.id and emp.salary > mng.salary;


### Write a solution to find all customers who never order anything.

select * from customers where id not in (
    select customerId from orders
)

### https://leetcode.com/problems/find-customer-referee/description/

select name from Customers where referee_id is null or referee_id != 2;


### https://leetcode.com/problems/customer-placing-the-largest-number-of-orders/description/

select customer_number from Orders group by customer_number order by count(customer_number) DESC limit 1;


### https://leetcode.com/problems/sales-person/

SELECT name 
FROM SalesPerson 
WHERE sales_id NOT IN (
    SELECT o.sales_id 
    FROM Orders o
    JOIN Company c ON o.com_id = c.com_id
    WHERE c.name = 'RED'
);


### https://leetcode.com/problems/not-boring-movies/

select * from Cinema where description != 'boring' and id%2!=0 order by rating desc;


### https://leetcode.com/problems/actors-and-directors-who-cooperated-at-least-three-times/

select actor_id, director_id from ActorDirector group by actor_id, director_id having count(*) >= 3;

### https://leetcode.com/problems/user-activity-for-the-past-30-days-i/description/

select activity_date, COUNT(DISTINCT user_id) as active_user from Activity 
where activity_date >= '2019-07-27'::date - INTERVAL '30 days'
group by activity_date;


### https://leetcode.com/problems/average-selling-price/description/
SELECT
    p.product_id,
    COALESCE(
        ROUND(
            SUM(p.price * u.units)::NUMERIC
            / NULLIF(SUM(u.units), 0),
            2
        ),
        0
    ) AS average_price
FROM Prices AS p
LEFT JOIN UnitsSold AS u
    ON p.product_id = u.product_id
    AND u.purchase_date BETWEEN p.start_date AND p.end_date
GROUP BY p.product_id;


### https://leetcode.com/problems/students-and-examinations/description/

SELECT 
    s.student_id, 
    s.student_name, 
    sub.subject_name, 
    COUNT(e.subject_name) AS attended_exams
FROM Students s
CROSS JOIN Subjects sub
LEFT JOIN Examinations e 
    ON s.student_id = e.student_id 
    AND sub.subject_name = e.subject_name
GROUP BY s.student_id, s.student_name, sub.subject_name
ORDER BY s.student_id, sub.subject_name;


### https://leetcode.com/problems/list-the-products-ordered-in-a-period/description/

select pd.product_name, sum(unit) as unit from Products as pd join Orders as ord on pd.product_id = ord.product_id
where DATE_PART('month', ord.order_date) = 2
group by ord.product_id, pd.product_name having sum(ord.unit) >= 100;


### https://leetcode.com/problems/group-sold-products-by-the-date/description/

select sell_date, count(distinct product) as num_sold, STRING_AGG(product, ',' order by product ASC) as products from Activities group by sell_date;

### https://leetcode.com/problems/game-play-analysis-i/description/

select player_id, min(event_date) as first_login from Activity group by player_id;


### https://leetcode.com/problems/friend-requests-ii-who-has-the-most-friends/description/

select id, count(*) as num
 from (
 	select requester_id as id from RequestAccepted
	 union all
	select accepter_id as id from RequestAccepted
 ) t
 group by id
 order by num DESC limit 1;


### https://leetcode.com/problems/trips-and-users/description/

SELECT Request_at AS Day, ROUND(SUM(CASE when status = 'completed' then 0 ELSE 1 end)::numeric/COUNT(Status), 2) AS "Cancellation Rate"
FROM Trips 
WHERE Client_Id NOT IN (SELECT Users_Id FROM Users WHERE Banned = 'Yes') 
    AND Driver_Id NOT IN (SELECT Users_Id FROM Users WHERE Banned = 'Yes')
    AND Request_at BETWEEN '2013-10-01' AND '2013-10-03'
GROUP BY Request_at;

