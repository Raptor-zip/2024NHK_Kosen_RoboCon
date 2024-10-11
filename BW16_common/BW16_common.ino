#include <WiFi.h>
#include <WiFiUDP.h>

#define IP_SEGMENT 11 // 192.168.--.**の--の部分
#define IP_HOST 44    // 192.168.--.**の**の部分
// DEVICE_IDをロボットまたはコントローラーに合わせてコメントアウト
#define DEVICE_ID "R1"
// #define DEVICE_ID "R22"
// #define DEVICE_ID "R23"
// #define DEVICE_ID "P2"
// #define DEVICE_ID "P3"

uint8_t CMB_R = PA26; // UserLED pin
uint8_t CMB_G = PA25; // UserLED pin
uint8_t CMB_B = PA30; // UserLED pin

#define M_SIZE 6                   // command_id (2 bytes) + pvalue (4 bytes)
#define LocalPort 8000             // BW16のコマンド受信ポート
#define RemotePort 8001            // ONEXのコマンド受信ポート
#define RemotePort_Connection 8002 // 自分のロボット名とIPを伝えるときのONEXの受信ポート

char ssid[] = "**";
char pass[] = "**";
WiFiUDP udp;
IPAddress RemoteIP;
typedef union
{
  uint8_t bin[4];
  uint32_t ui32;
  int32_t i32;
  float f;
} UDP_Content_TypeDef;
UDP_Content_TypeDef udp_content;
bool RemoteIP_ready = false; // ONEXのIPが取得出来たらtrueになる

uint8_t send_count = 1; // 送信カウントの初期値
uint8_t led_r_toggle = 0;
uint8_t led_b_toggle = 0;

uint32_t last_millis = 0;
uint16_t send_RSSI_timer = 0;
uint32_t send_connection_timer = 0;

float temp_last_float;

void setup()
{
  Serial.begin(921600);

  if (strcmp(DEVICE_ID, "P2") == 0 || strcmp(DEVICE_ID, "P3") == 0)
  {
    CMB_R = PA30;
    CMB_G = PA30;
    CMB_B = PA30;
  }

  pinMode(CMB_R, OUTPUT);
  pinMode(CMB_G, OUTPUT);
  pinMode(CMB_B, OUTPUT);

  while (WiFi.status() != WL_CONNECTED)
  {
    digitalWrite(CMB_G, HIGH);
    Serial.println("WiFi接続中");

    WiFi.config(IPAddress(192, 168, IP_SEGMENT, IP_HOST));
    WiFi.begin(ssid, pass);
    digitalWrite(CMB_G, LOW);
    delay(100);
  }
  Serial.println("WiFi接続成功");
  digitalWrite(CMB_G, LOW);

  Serial1.begin(1000000);
  udp.setRecvTimeout(10);
  udp.begin(LocalPort);
}

// UDP経由でRSSI値を送信
void UDP_SendRSSI()
{
  if (send_RSSI_timer > 1005)
  {
    send_RSSI_timer = 0;

    int32_t RSSI = WiFi.RSSI();
    UDP_Send(0xFFF0, (uint8_t *)&RSSI);
  }
  send_RSSI_timer++;
}

// DEVICE_IDをUDP経由で送信し、接続状態を通知
void UDP_SendConnection()
{
  if (send_connection_timer > 1000)
  {
    send_connection_timer = 0;
    if (RemoteIP_ready)
    {
      udp.beginPacket(RemoteIP, RemotePort_Connection);
      udp.print(DEVICE_ID);
      udp.endPacket();
    }
  }
  send_connection_timer++;
}

void loop()
{
  UDP_Receive();
  UART_Receive();

  if (millis() != last_millis)
  {
    // 1ms timer
    if (WiFi.status() != WL_CONNECTED)
      setup(); // WiFiが接続されていないならsetup()
    UDP_SendRSSI();
    UDP_SendConnection();
  }
  last_millis = millis();
}

// UDPパケットを送信
void UDP_Send(uint16_t command_id, uint8_t *pvalue)
{
  if (RemoteIP_ready)
  {
    uint8_t senddata[M_SIZE];
    memcpy(&senddata[0], &command_id, sizeof(command_id));
    memcpy(&senddata[2], pvalue, sizeof(uint32_t));
    udp.beginPacket(RemoteIP, RemotePort);
    udp.write(senddata, M_SIZE);
    udp.endPacket();
    led_r_toggle = !led_r_toggle;
    digitalWrite(CMB_R, led_r_toggle);
  }
  else
  {
    Serial.print(__LINE__);
    Serial.println(": ONEXのIPアドレス不明のため送信不可");
  }
}

// 受信したデータを基にリモートIPを設定
void UDP_Set_RemoteIP(uint8_t *ipadr)
{
  RemoteIP = IPAddress(ipadr[0], ipadr[1], ipadr[2], ipadr[3]);
  RemoteIP_ready = true;
}

// 受信したコマンドに基づいて動作を実行
void command_action(uint16_t command_id, uint8_t *pvalue)
{
  // if (command_id == 0x4a1 || command_id == 0x490) {
  //   memcpy(udp_content.bin, pvalue, sizeof(udp_content.bin));
  //   if(udp_content.f - temp_last_float > 1.5){
  //     Serial.println();
  //     Serial.println();
  //     Serial.println("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
  //     Serial.println();
  //   }else{
  //     Serial.println(udp_content.f);
  //   }
  //   temp_last_float = udp_content.f;
  // }  // TODO
  // UDP_Send(command_id, pvalue); // オウム返し
  switch (command_id)
  {
  case 0xFFF1:
    // Pingを受信したとき
    UDP_Send(0xFFF2, pvalue); // Pongを返す
    break;

  case 0xFFFF:
    UDP_Set_RemoteIP(pvalue); // ONEXのIPを保存
    break;

  default:
    uint8_t buffer[M_SIZE + 2];         // count (1 byte) + command_id (2 bytes) + pvalue (4 bytes) + count (1 byte) = 8 bytes
    buffer[0] = send_count;             // 送信カウントを追加
    memcpy(buffer + 1, &command_id, 2); // command_idのデータをバッファにコピー
    memcpy(buffer + 3, pvalue, 4);      // pvalueのデータをバッファにコピー
    buffer[7] = send_count;
    Serial1.write(buffer, M_SIZE + 2); // UARTでSTM32にデータを送信 // TODO直す
    // delay(1);
    send_count = (send_count == 255) ? 1 : send_count + 1; // 送信カウントをインクリメント、255に達したら1に戻す
    break;
  }
}

// UDPパケットを受信し、コマンドを処理
void UDP_Receive()
{
  if (udp.parsePacket())
  {
    uint8_t recdata[M_SIZE * 10];
    uint8_t received_size = udp.read(recdata, M_SIZE * 10);

    for (uint8_t i = 0; i < received_size / 6; i++)
    {
      uint16_t command_id = 0;
      memcpy(&command_id, &recdata[i * 6], sizeof(command_id));
      command_action(command_id, &recdata[2 + i * 6]);
    }
    led_b_toggle = !led_b_toggle;
    digitalWrite(CMB_B, led_b_toggle);

    // uint16_t command_id = 0;
    // memcpy(&command_id, &recdata[0], sizeof(command_id));
    // command_action(command_id, &recdata[2]);
  }
}

// UARTで受信したデータを処理
void UART_Receive()
{
  if (Serial1.available())
  {
    uint8_t uart_received[M_SIZE] = {};
    Serial1.readBytes(uart_received, M_SIZE);
    uint16_t command_id = 0;
    memcpy(&command_id, &uart_received[0], sizeof(command_id));
    // print_uart_received(uart_received, sizeof(uart_received));
    UDP_Send(command_id, &uart_received[2]);
  }
}

void print_uart_received(uint8_t *uart_received, size_t length)
{
  // 配列の各要素を表示
  for (size_t i = 0; i < length; i++)
  {
    Serial.print(uart_received[i], HEX); // HEX表記で表示する場合
    Serial.print(" ");
  }
  Serial.println(); // 改行
}
