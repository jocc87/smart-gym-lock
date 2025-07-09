SELECT * FROM pg_trigger WHERE tgrelid = 'orders'::regclass;
SELECT status FROM orders WHERE id = 2;
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'create_right_on_order';
select * from rights where user_id = '158';
select * from users where id = '158';


CREATE OR REPLACE FUNCTION create_right_on_order()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'paid' THEN
    -- nézzük meg, van-e már jog ezzel az order_id-vel
    IF NOT EXISTS (
      SELECT 1 FROM rights WHERE order_id = NEW.id
    ) THEN
      INSERT INTO rights (
        user_id, lock_id, access_type, access_value, valid_from, valid_until, order_id
      ) VALUES (
        NEW.user_id,
        5716380,
        'passcode',
        NEW.passcode,
        NOW(),
        NOW() + INTERVAL '30 days',
        NEW.id
      );
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;



DROP TRIGGER IF EXISTS trg_order_to_right ON orders;

CREATE TRIGGER trg_order_to_right
AFTER INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION create_right_on_order();



CREATE OR REPLACE FUNCTION create_right_on_order()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'paid' THEN
    INSERT INTO rights (
      user_id, lock_id, access_type, access_value, valid_from, valid_until
    ) VALUES (
      NEW.user_id,
      5716380,
      'passcode',
      NEW.passcode,
      NOW(),
      NOW() + INTERVAL '30 days'
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_order_paid_update ON orders;

CREATE TRIGGER trg_order_paid_update
AFTER UPDATE ON orders
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION create_right_on_order();

#tárolt eljárás nyitások összesítése felhasználónként
CREATE OR REPLACE FUNCTION user_open_stats()
RETURNS TABLE (
    username TEXT,
    nyitasok INTEGER,
    sikeres INTEGER,
    sikertelen INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        logs.username::TEXT,
        COUNT(*)::INTEGER AS nyitasok,
        COUNT(*) FILTER (WHERE logs.success = true)::INTEGER AS sikeres,
        COUNT(*) FILTER (WHERE logs.success = false)::INTEGER AS sikertelen
    FROM logs
    GROUP BY logs.username
    HAVING COUNT(*) > 1;
END;
$$;

SELECT * FROM user_open_stats();