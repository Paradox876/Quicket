<?php
class Database {
    private static $connection;

    public static function connect() {
        if (!self::$connection) {
            try {
                self::$connection = new PDO(
                    "sqlsrv:Server=" . getenv('DB_HOST') . ";Database=" . getenv('DB_NAME'),
                    getenv('DB_USER'),
                    getenv('DB_PASS'),
                    [
                        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                        PDO::SQLSRV_ATTR_ENCODING => PDO::SQLSRV_ENCODING_UTF8
                    ]
                );
            } catch (PDOException $e) {
                error_log("Database error: " . $e->getMessage());
                throw new Exception("Database connection failed");
            }
        }
        return self::$connection;
    }
}
?>