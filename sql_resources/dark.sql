drop database if exists Dark_Academy;

create database if not exists Dark_Academy
character set utf8mb4
collate utf8mb4_spanish_ci;

use Dark_Academy;

drop table if exists alumnos;
create table alumnos(
    expediente char(8) PRIMARY KEY,
    nombre varchar(30) NOT NULL,
    apellidos varchar(50) NOT NULL
);

insert into alumnos values
    ('11111111', 'Alexia', 'Núñez Pérez'), 
    ('22222222', 'Rosa', 'Fernández Oliva'), 
    ('33333333', 'Peter', 'Linuesa Jiménez'), 
    ('44444444', 'Juan Carlos', 'Wesnoth The Second'), 
    ('55555555', 'Federico', 'Muñoz Ferrer'); 

-- select * from alumnos;
drop table if exists modulos;
create table modulos(
    codigo varchar(5) PRIMARY KEY,
    nombre varchar(30) NOT NULL
);

insert into modulos values 
    ('QP', 'Quirománcia Práctica'), 
    ('MR', 'Mortum Redivivus'), 
    ('RF', 'Refactorización Zómbica'), 
    ('ARF', 'Ampliación de RF'),
    ('OP', 'Orquestación de Plagas');

drop table if exists notas;
create table notas(
    expediente char(8),
    codigo varchar(5),
    nota integer unsigned,
    PRIMARY KEY (expediente, codigo),
    constraint fk_expediente 
        foreign key (expediente)
        references alumnos(expediente)
        on delete cascade on update cascade,
    constraint fk_codigo
        foreign key (codigo)
        references modulos(codigo)
        on delete cascade on update cascade
);

/* PREGUNTA 3: (3 puntos) Diseña tres triggers que hagan una auditoría de todos
los cambios hechos en la tabla notas. Se auditarán inserciones, borrados y modificaciones.
Se proporciona la tabla para auditar */
drop table if exists auditoria_notas;
create table auditoria_notas(
    id serial PRIMARY KEY, -- clave autoincremental
    expediente_old char(8), -- expediente viejo
    codigo_old varchar(5), -- módulo viejo
    nota_old integer unsigned, -- nota antigua
    expediente_new char(8), -- expediente nuevo
    codigo_new varchar(5), -- módulo nuevo
    nota_new integer unsigned, -- nota nueva
    usuario varchar(50) not null, -- usuario que hace la modificación
    cuando datetime not null, -- fecha y hora de la modificación
    operacion enum('insert', 'update', 'delete') not null -- operación DML utilizada
);
delimiter ;
drop trigger if exists auditoria_notas_insert;

create trigger auditoria_notas_insert after insert on notas
for each row
    insert into auditoria_notas 
    values(null, null, null, null, new.expediente, new.codigo, new.nota, user(), now(), 'insert');

delimiter ;
drop trigger if exists auditoria_notas_update;

create trigger auditoria_notas_update after update on notas
for each row
    insert into auditoria_notas 
    values(null, old.expediente, old.codigo, old.nota, new.expediente, new.codigo, new.nota, user(), now(), 'update');

delimiter ;
drop trigger if exists auditoria_notas_delete;

create trigger auditoria_notas_delete after delete on notas
for each row
    insert into auditoria_notas 
    values(null, old.expediente, old.codigo, old.nota, null, null, null, user(), now(), 'delete');

insert into notas values 
    ('11111111', 'QP', 5), 
    ('11111111', 'MR', 7), 
    ('11111111', 'RF', 6), 
    ('11111111', 'ARF', 9), 
    ('11111111', 'OP', 7), 
    ('22222222', 'QP', NULL), 
    ('22222222', 'MR', 5), 
    ('22222222', 'RF', 5), 
    ('22222222', 'ARF', 6), 
    ('22222222', 'OP', NULL), 
    ('33333333', 'QP', 9), 
    ('33333333', 'MR', 5),
    ('33333333', 'RF', 6), 
    ('33333333', 'ARF', 4),
    ('33333333', 'OP', 6), 
    ('44444444', 'QP', 4),
    ('44444444', 'MR', 6),
    ('44444444', 'RF', 8),
    ('44444444', 'ARF', 6),
    ('44444444', 'OP', 5),
    ('55555555', 'QP', 8),
    ('55555555', 'MR', 4),
    ('55555555', 'RF', NULL),
    ('55555555', 'ARF', NULL),
    ('55555555', 'OP', 4);


/* PREGUNTA 1 (1 punto): Diseña una función que compruebe si un expediente es correcto.
Un expediente correcto debe tener 8 dígitos numéricos 
A la función se le pasará un char(8) como parámetro y 
retornará un boolean (0 o False, 1 o True) */
drop function if exists expediente_correcto;
delimiter //
create function expediente_correcto(exp char(8)) returns BOOLEAN
DETERMINISTIC
NO SQL
begin
    return (exp regexp '^[0-9]{8}$');
end//

delimiter ;

-- select expediente_correcto('aba');
-- select expediente_correcto('01222455');
-- select expediente_correcto('a1010011');


/* PREGUNTA 2: (2 puntos) Diseña un trigger que antes de insertar un 
alumno haga lo siguiente:
 - Si el expediente es incorrecto: se impide la inserción con 
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '....' en el mensaje de error 
 debe aparecer el código de expediente erróneo.
 - Si el expediente es correcto: Se pasa el nombre y apellidos a mayúsculas
 para que se inserten de esa manera */

drop trigger if exists alumnos_check_bi;

delimiter //

create trigger alumnos_check_bi before insert on alumnos
for each row
begin
    declare msg varchar(50);
    if not expediente_correcto(new.expediente) then
        set msg = concat('expediente incorrecto --> ', new.expediente);
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = msg;
    else
        set new.nombre = upper(new.nombre);
        set new.apellidos = upper(new.apellidos);
    end if;
end//

delimiter ;

-- delete from alumnos where Expediente = '12121212';
-- insert into alumnos values('malexp01', 'Tanos', 'Super Villano');
-- insert into alumnos values ('12121212', 'Tanos', 'Supervillano');
-- select * from alumnos;

/* PREGUNTA 4: (4 puntos) diseña un procedimiento almacenado que genere una tabla con los alumnos 
que pasan a segundo del ciclo 'Artes Oscuras'. La tabla se llamará alumnos_segundo y tiene la
misma estructura que la tabla alumnos. El procedimiento también debe devolver el porcentaje
de alumnos que pasan a segundo. Los requisitos que debe cumplir un alumno para pasar
a segundo son: tener todos los módulos con nota y que la media de las notas sea mayor o igual a 6. 
Si un alumno no se ha examinado de un módulo entonces su nota es NULL y, obviamente, ya no pasa a 
segundo */

drop procedure if exists pasan_segundo;

delimiter //

create procedure pasan_segundo(OUT porcentaje varchar(10))
begin
    -- variables locales
    declare total integer unsigned default 0;
    declare contador integer unsigned default 0;
    declare salir boolean default False;
    -- variables locales para el cursor
    declare cexpediente char(8);
    declare cavg float;
    declare ccount integer unsigned;
    -- cursor
    declare cnotas cursor for
        select expediente, AVG(nota), count(nota) 
        from notas 
        where nota is not null
        group by expediente;
    -- handler para salir del bucle
    declare continue handler for NOT FOUND set salir = True;
    
    -- creación tabla
    drop table if exists alumnos_segundo;
    create table alumnos_segundo like alumnos;

    -- para el porcentaje: total de alumnos
    select count(*) into total from alumnos;

    open cnotas;
    while not salir do
        fetch cnotas into cexpediente, cavg, ccount;
        if not salir then
            if ccount = 5 and cavg >= 6.0 then
                insert into alumnos_segundo
                    select * from alumnos where expediente = cexpediente;
            end if;
        end if;
    end while;
    -- para el porcentaje obtengo la cantidad que pasa a segundo
    select count(*) into contador from alumnos_segundo;
    -- cálculo del porcentaje y paso a cadena
    set porcentaje = concat(CAST(contador*100/total AS CHAR), '%');

end//

delimiter ;

-- delete from alumnos where Expediente = '12121212';
call pasan_segundo(@porcentaje);
select expediente, AVG(nota), count(nota) 
        from notas 
        where nota is not null
        group by expediente;

-- select * from alumnos;
-- select * from alumnos_segundo;
-- select @porcentaje;

