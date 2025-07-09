from langchain_core.tools import tool
from app.service.agent.models import (
    OrderInput,
    GetProductByUserID,
    OrderStatusInput,
    OrderCancelInput,
    OrderUpdateInput,
    SendImageProductToCustomer,
)
from config.postgresql import get_db
from datetime import datetime, timedelta
from sqlalchemy import text
import uuid, logging
from app.service.chromadb import vectorstore
import requests, asyncio
from app.service.agent.services.send_message_to_admin import (
    send_message_to_admin_service_async,
    send_image_to_admin_service_async,
)

logger = logging.getLogger(__name__)


def create_tools(user_id: str):
    """Create tools for the agent"""

    @tool(args_schema=OrderInput)
    async def save_order(
        customer_name: str,
        product_name: str,
        quantity: int,
        level_ice: str,
        level_sugar: str,
        temperature: str,
        status: str = "ON-PROCESS",
    ):
        """
        Simpan detail pesanan pelanggan ke dalam database.

        Gunakan tool ini HANYA SETELAH kamu mengkonfirmasi SEMUA detail pesanan
        (nama pelanggan, nama produk, jumlah, level es, level gula, temperature) dengan pelanggan
        dan pelanggan sudah setuju untuk membuat pesanan. atau jika di rasa pelanggan sudah intensi oke langsung simpan saja pesanan agar tidak menunggu.

        Args:
            customer_name: Nama lengkap pelanggan.
            product_name: nama dari produk yang dipesan.
            quantity: Jumlah produk yang dipesan.
            level_ice: Level ice yang dipesan.
            level_sugar: Level sugar yang dipesan.
            temperature: Temperatur yang dipesan panas atau dingin.
            status: Status pemesanan default ON-PROCESS.

        Returns:
            Pesan konfirmasi berisi nomor pesanan jika berhasil, atau pesan error jika gagal.
        """
        print(f"--- MENYIMPAN PESANAN UNTUK: {customer_name} ---")  # Untuk debugging
        order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        try:
            async for db in get_db():
                try:
                    query = text(
                        """
                            INSERT INTO orders (customer_name, product_name, level_ice,level_sugar,temperature,status,quantity,order_id)
                            VALUES (:customer_name, :product_name, :level_ice,:level_sugar, :temperature,:status ,:quantity,:order_id)
                        """
                    )
                    await db.execute(
                        query,
                        {
                            "customer_name": customer_name,
                            "product_name": product_name,
                            "level_ice": level_ice,
                            "level_sugar": level_sugar,
                            "temperature": temperature,
                            "status": status,
                            "quantity": quantity,
                            "order_id": order_id,
                        },
                    )
                    await db.commit()

                    query = text(
                        """
                        SELECT order_id, customer_name, product_name, quantity, 
                               level_ice, level_sugar, temperature, status, order_time
                        FROM orders 
                        WHERE order_id = :order_id
                        """
                    )
                    result = await db.execute(query, {"order_id": order_id})
                    order = result.fetchone()
                    if order:
                        # Format status dengan emoji
                        status_emoji = {
                            "ON-PROCESS": "🔄",
                            "COMPLETED": "✅",
                        }

                        status_icon = status_emoji.get(order[0], "📋")

                        response = f"""
                            🔍 **STATUS PESANAN DITEMUKAN**

                            📋 **Detail Pesanan:**
                            - Nomor Pesanan: **{order[0]}**
                            - Nama Pelanggan: {order[1]}
                            - Produk: {order[2]}
                            - Jumlah: {order[3]}
                            - Level Es: {order[4]}
                            - Level Gula: {order[5]}
                            - Suhu: {order[6]}

                            {status_icon} **Status: {order[7]}**
                            📅 Tanggal Pesanan: {order[8].strftime('%d/%m/%Y %H:%M')}

                                                    """

                        await send_message_to_admin_service_async(message=response)

                    print("✅ Insert berhasil dengan ID:", product_name)
                except Exception as e:
                    await db.rollback()
                    print("❌ Gagal insert:", e)

            print(f"--- PESANAN BERHASIL DISIMPAN DENGAN NAMA: {customer_name} ---")
            return f"Pesanan berhasil dibuat. Nomor pesanan Anda adalah {order_id}. Mohon sampaikan ini kepada pelanggan."

        except Exception as e:
            # logger.error(f"Gagal menyimpan pesanan: {e}") # Praktik terbaik untuk logging
            print(f"--- ERROR SAAT MENYIMPAN PESANAN: {e} ---")
            return f"Terjadi kesalahan teknis saat menyimpan pesanan: {str(e)}. Mohon informasikan kepada pelanggan dan coba lagi nanti."

    @tool(args_schema=SendImageProductToCustomer)
    async def send_image_to_customer(name: str, user: str):
        """
        mengambil gambar/image_url products berdasarkan name dan user_id untuk mengambil gambar dan mengirim ke customer.
        Gunakan saat pelanggan minta gambar produk.

        Args:
            name: Nama lengkap pelanggan.
            user: User pemilik produk yang membuat didatabase.

        Returns:
            Pesan konfirmasi berisi gambar dari produk yang diminta.
        """
        print(f"--- CHECKING GAMBAR PRODUCT FOR: {name} ---")
        user = user_id
        try:
            async for db in get_db():
                try:
                    query = text(
                        """
                        SELECT name, image_url, description
                        FROM products 
                        WHERE name LIKE :name AND user_id = :user_id
                        """
                    )
                    result = await db.execute(
                        query, {"name": f"{name}%", "user_id": user}
                    )
                    product = result.fetchone()
                    print("✅Product Image : ", product[1])

                    if product:
                        image_url = product[1]
                        response = f"Ini gambar produk **{product[0]}**"

                        print(f"✅ product found: {product[0]}")
                        await send_image_to_admin_service_async(response, image_url)
                        return response.strip()
                    else:
                        print(f"❌ product gambar not found: {name}")
                        return f"❌ Gambar produk dengan nama **{name}** tidak ditemukan.\n\n💡 Cek lagi nama produk Anda."
                except Exception as e:
                    print(f"❌ Database error: {e}")
                    return f"Terjadi kesalahan saat mencari produk: {str(e)}"
        except Exception as e:
            print(f"--- ERROR CHECKING ORDER: {e} ---")
            return f"Terjadi kesalahan sistem saat mengecek produk: {str(e)}"

    @tool(args_schema=OrderStatusInput)
    async def check_order_status(order_id: str):
        """
        Cek status pesanan berdasarkan Order ID.

        Gunakan tool ini ketika pelanggan ingin mengetahui status pesanan mereka
        dengan memberikan nomor order ID (format: ORD-XXXXXXXXXXXX).

        Args:
            order_id: ID pesanan yang akan dicek statusnya

        Returns:
            Informasi detail pesanan dan status terkini
        """

        print(f"--- CHECKING ORDER STATUS FOR: {order_id} ---")

        try:
            async for db in get_db():
                try:
                    query = text(
                        """
                        SELECT order_id, customer_name, product_name, quantity, 
                               level_ice, level_sugar, temperature, status, order_time
                        FROM orders 
                        WHERE order_id = :order_id
                        """
                    )
                    result = await db.execute(query, {"order_id": order_id})
                    order = result.fetchone()
                    if order:
                        # Format status dengan emoji
                        status_emoji = {
                            "ON-PROCESS": "🔄",
                            "COMPLETED": "✅",
                        }

                        status_icon = status_emoji.get(order[0], "📋")

                        response = f"""
                            🔍 **STATUS PESANAN DITEMUKAN**

                            📋 **Detail Pesanan:**
                            - Nomor Pesanan: **{order[0]}**
                            - Nama Pelanggan: {order[1]}
                            - Produk: {order[2]}
                            - Jumlah: {order[3]}
                            - Level Es: {order[4]}
                            - Level Gula: {order[5]}
                            - Suhu: {order[6]}

                            {status_icon} **Status: {order[7]}**
                            📅 Tanggal Pesanan: {order[8].strftime('%d/%m/%Y %H:%M')}

                            {'🎉 Pesanan Anda sudah selesai! Silakan diambil.' if order[7] == 'COMPLETED' else '⏳ Pesanan sedang diproses, mohon menunggu sebentar.'}
                                                    """

                        print(f"✅ Order found: {order[0]} - Status: {order[7]}")
                        return response.strip()
                    else:
                        print(f"❌ Order not found: {order_id}")
                        return f"❌ Pesanan dengan ID **{order_id}** tidak ditemukan.\n\n💡 Pastikan nomor pesanan yang Anda masukkan benar atau hubungi admin untuk bantuan."

                except Exception as e:
                    print(f"❌ Database error: {e}")
                    return f"Terjadi kesalahan saat mencari pesanan: {str(e)}"

        except Exception as e:
            print(f"--- ERROR CHECKING ORDER: {e} ---")
            return f"Terjadi kesalahan sistem saat mengecek status pesanan: {str(e)}"

    @tool(args_schema=OrderCancelInput)
    async def cancel_order(order_id: str, reason: str = ""):
        """
        Batalkan pesanan dengan mengubah status menjadi CANCELLED.

        Gunakan tool ini ketika pelanggan ingin membatalkan pesanan mereka.
        Pesanan hanya bisa dibatalkan jika statusnya masih ON-PROCESS atau PREPARING.

        Args:
            order_id: ID pesanan yang akan dibatalkan
            reason: Alasan pembatalan (opsional)

        Returns:
            Konfirmasi pembatalan atau pesan error jika tidak bisa dibatalkan
        """
        print(f"--- ATTEMPTING TO CANCEL ORDER: {order_id} ---")

        try:
            async for db in get_db():
                try:
                    # Cek apakah order exists dan statusnya
                    check_query = text(
                        """
                        SELECT order_id, customer_name, product_name, status, order_time
                        FROM orders 
                        WHERE order_id = :order_id
                    """
                    )
                    result = await db.execute(check_query, {"order_id": order_id})
                    order = result.fetchone()

                    if not order:
                        print(f"❌ Order not found: {order_id}")
                        return f"❌ Pesanan dengan ID **{order_id}** tidak ditemukan."

                    # Validasi time window (contoh: hanya bisa cancel dalam 30 menit)
                    time_limit = timedelta(minutes=30)
                    if datetime.now() - order[4] > time_limit:
                        print(f"❌ Time limit exceeded for order {order_id}")
                        return f"❌ Pesanan **{order_id}** sudah melewati batas waktu pembatalan (30 menit).\n\n💡 Hubungi admin untuk bantuan."

                    # Update status menjadi CANCELLED
                    cancel_query = text(
                        """
                        UPDATE orders 
                        SET status = 'CANCELLED'
                        WHERE order_id = :order_id
                    """
                    )

                    await db.execute(
                        cancel_query,
                        {
                            "order_id": order_id,
                        },
                    )
                    await db.commit()
                    response = f"""
                    ✅ **PESANAN BERHASIL DIBATALKAN**

                    📋 **Detail Pesanan:**
                    - Nomor Pesanan: **{order_id}**
                    - Nama Pelanggan: {order[1]}
                    - Produk: {order[2]}
                    - Status: ❌ **CANCELLED**

                    📝 **Alasan:** {reason or "Dibatalkan oleh pelanggan"}

                    💡 Jika ada pertanyaan, hubungi admin untuk bantuan.
                    """

                    print(f"✅ Order {order_id} successfully cancelled")
                    return response.strip()

                except Exception as e:
                    await db.rollback()
                    print(f"❌ Database error during cancellation: {e}")
                    return f"Terjadi kesalahan saat membatalkan pesanan: {str(e)}"

        except Exception as e:
            print(f"--- ERROR CANCELLING ORDER: {e} ---")
            return f"Terjadi kesalahan sistem saat membatalkan pesanan: {str(e)}"

    @tool(args_schema=OrderUpdateInput)
    async def update_order(
        order_id: str,
        customer_name: str = None,
        product_name: str = None,
        quantity: int = None,
        level_ice: str = None,
        level_sugar: str = None,
        temperature: str = None,
    ):
        """
        Update detail pesanan yang sudah ada.

        Gunakan tool ini ketika pelanggan ingin mengubah detail pesanan mereka.
        Pesanan hanya bisa diupdate jika statusnya masih ON-PROCESS. Tapi batas waktu 10 menit saja, jika lewat maka tidak bisa.
        Hanya field yang diisi yang akan diupdate.

        Args:
            order_id: ID pesanan yang akan diupdate
            customer_name: Nama pelanggan baru (opsional)
            product_name: Nama produk baru (opsional)
            quantity: Jumlah produk baru (opsional)
            level_ice: Level ice baru (opsional)
            level_sugar: Level sugar baru (opsional)
            temperature: Temperatur baru (opsional)

        Returns:
            Konfirmasi update atau pesan error jika tidak bisa diupdate
        """
        print(f"--- ATTEMPTING TO UPDATE ORDER: {order_id} ---")

        # Validasi: minimal satu field harus diisi
        update_fields = {
            "customer_name": customer_name,
            "product_name": product_name,
            "quantity": quantity,
            "level_ice": level_ice,
            "level_sugar": level_sugar,
            "temperature": temperature,
        }

        fields_to_update = {k: v for k, v in update_fields.items() if v is not None}

        if not fields_to_update:
            return "❌ Tidak ada field yang akan diupdate. Mohon tentukan minimal satu field yang ingin diubah."

        try:
            async for db in get_db():
                try:
                    # Cek apakah order exists dan statusnya
                    check_query = text(
                        """
                        SELECT order_id, customer_name, product_name, quantity, 
                            level_ice, level_sugar, temperature, status, order_time
                        FROM orders 
                        WHERE order_id = :order_id
                    """
                    )
                    result = await db.execute(check_query, {"order_id": order_id})
                    order = result.fetchone()
                    print(f"Order found: {order}")
                    if not order:
                        print(f"❌ Order not found: {order_id}")
                        return f"❌ Pesanan dengan ID **{order_id}** tidak ditemukan."

                    # Validasi apakah order bisa diupdate
                    if order[7] != "ON-PROCESS":
                        status_messages = {
                            "PREPARING": "sudah dalam proses pembuatan",
                            "READY": "sudah siap untuk diambil",
                            "COMPLETED": "sudah selesai",
                            "CANCELLED": "sudah dibatalkan",
                        }
                        status_msg = status_messages.get(
                            order[7], f"dalam status {order[7]}"
                        )

                        print(f"❌ Cannot update order {order_id}: status {order[7]}")
                        return f"❌ Pesanan **{order_id}** tidak dapat diubah karena {status_msg}.\n\n💡 Hubungi admin jika ada masalah."

                    # Validasi time window (contoh: hanya bisa update dalam 15 menit)
                    time_limit = timedelta(minutes=15)
                    if datetime.now() - order[8] > time_limit:
                        print(f"❌ Time limit exceeded for order {order_id}")
                        return f"❌ Pesanan **{order_id}** sudah melewati batas waktu untuk diubah (15 menit).\n\n💡 Hubungi admin untuk bantuan."

                    # Build dynamic update query
                    set_clauses = []
                    params = {"order_id": order_id}

                    for field, value in fields_to_update.items():
                        set_clauses.append(f"{field} = :{field}")
                        params[field] = value

                    update_query = text(
                        f"""
                        UPDATE orders 
                        SET {', '.join(set_clauses)}
                        WHERE order_id = :order_id
                        """
                    )

                    await db.execute(update_query, params)
                    await db.commit()
                    # Log update untuk audit trail
                    # Get updated order data untuk response
                    updated_result = await db.execute(
                        check_query, {"order_id": order_id}
                    )
                    updated_order = updated_result.fetchone()

                    # Log perubahan yang dilakukan
                    changes = []
                    field_names = {
                        "customer_name": "Nama Pelanggan",
                        "product_name": "Produk",
                        "quantity": "Jumlah",
                        "level_ice": "Level Es",
                        "level_sugar": "Level Gula",
                        "temperature": "Temperatur",
                    }

                    for field, new_value in fields_to_update.items():
                        field_index = {
                            "customer_name": 1,
                            "product_name": 2,
                            "quantity": 3,
                            "level_ice": 4,
                            "level_sugar": 5,
                            "temperature": 6,
                        }
                        old_value = order[field_index[field]]
                        if old_value != new_value:
                            changes.append(
                                f"{field_names[field]}: {old_value} → {new_value}"
                            )

                    response = f"""
                    ✅ **PESANAN BERHASIL DIUPDATE**

                    📋 **Detail Pesanan Terbaru:**
                    - Nomor Pesanan: **{updated_order[0]}**
                    - Nama Pelanggan: {updated_order[1]}
                    - Produk: {updated_order[2]}
                    - Jumlah: {updated_order[3]}
                    - Level Es: {updated_order[4]}
                    - Level Gula: {updated_order[5]}
                    - Temperatur: {updated_order[6]}
                    - Status: 🔄 **{updated_order[7]}**

                    📝 **Perubahan yang Dilakukan:**
                    {chr(10).join(f"• {change}" for change in changes) if changes else "• Tidak ada perubahan"}

                    💡 Pesanan Anda telah diperbarui dan akan diproses sesuai detail terbaru.
                                    """

                    print(f"✅ Order {order_id} successfully updated")
                    return response.strip()

                except Exception as e:
                    await db.rollback()
                    print(f"❌ Database error during update: {e}")
                    return f"Terjadi kesalahan saat mengupdate pesanan: {str(e)}"

        except Exception as e:
            print(f"--- ERROR UPDATING ORDER: {e} ---")
            return f"Terjadi kesalahan sistem saat mengupdate pesanan: {str(e)}"

    @tool
    def search_user_knowledge(query: str) -> str:
        """
        Cari informasi produk dari vectordatabase.

        Tool ini akan:
        1. Mencari produk di vectordatbase terlebih dahulu (akurat & real-time)
        2. Jika tidak ditemukan, baru cari di vector knowledge base
        3. Selalu menampilkan harga dan informasi lengkap
        Digunakan saat pengguna menanyakan produk, layanan, panduan, atau FAQ.
        """
        try:
            results = vectorstore.similarity_search(
                query, k=3, filter={"user_id": user_id}
            )
            return (
                results[0].page_content
                if results
                else "Tidak ditemukan informasi relevan."
            )
        except Exception as e:
            return f"Terjadi kesalahan: {str(e)}"

    @tool(args_schema=GetProductByUserID)
    async def get_product_menu(user: str = None) -> str:
        """
        Tampilkan menu produk lengkap dengan harga.

        Gunakan tool ini ketika pelanggan ingin melihat:
        - Semua produk yang tersedia
        - Daftar harga lengkap

        Args:
            user: ID pengguna (opsional)
        """
        user = user_id
        logger.info(f"📋 Getting product menu dari User: {user or 'all'}")

        try:
            async for db in get_db():
                query = text(
                    """
                    SELECT name, description, price
                    FROM products
                    WHERE user_id = :user_id
                """
                )
                result = await db.execute(query, {"user_id": user})
                products = result.mappings().all()

                if not products:
                    return "❌ Tidak ada produk yang tersedia saat ini."

                # Format menu
                response = ["🍽️ **MENU PRODUK**\n"]

                for product in products:
                    price_formatted = f"Rp {product['price']:,.0f}".replace(",", ".")
                    item_line = f"• **{product['name']}** - {price_formatted}"
                    if product["description"]:
                        item_line += f"\n  _{product['description']}_"
                    response.append(item_line)

                response.append(
                    "\n💡 **Info:** Untuk memesan, sebutkan nama produk dan detail pesanan Anda!"
                )

                return "\n".join(response)

        except Exception as e:
            logger.error(f"❌ Gagal mengambil menu: {e}")
            return f"❌ Terjadi kesalahan saat mengambil menu: {str(e)}"

    local_tools = [
        search_user_knowledge,
        save_order,
        check_order_status,
        cancel_order,
        update_order,
        get_product_menu,
        send_image_to_customer,
    ]

    return local_tools


def send_message_to_admin_service(message: str):
    try:
        req = requests.post(
            "http://arisbara.cloud:3414/send-message",
            data={
                "session_id": "edb0439d-2bb2-44fd-94b7-272c2a166506",
                "to": "082157704435",
                "message": message,
            },
        )
        return req.json()
    except Exception as e:
        logger.error(f"Notification sending failed: {e}")
        return False
