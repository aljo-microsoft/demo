package main

import (
	"crypto/tls"
  "encoding/json"
	"fmt"
	"html/template"
  "io/ioutil"
	"log"
	"net/http"
	"net"
	"os"
  "gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
  "time"
)

var (
	database string
	password string
	port string
	username string
)

// DBPassword.txt file name is defined within packages configuration
// SECURE_STORE_SERVICE_DISTINATION is absolute path defined within ApplicationManifest.xml where secrets will be accessible.
// ENVIRONMENT_DATABASE_NAME is a parameterized EnvironmentOverride defined within ApplicationManifest.xml 
func init() {
	database = os.Getenv("DATABASE_NAME")
	username = os.Getenv("DB_USER_NAME")
  port = ":8080"
  
  // Get Access Token
    req, err := http.NewRequest("GET", "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F", nil)
    if err != nil {
        // handle err
    }
    req.Header.Set("Metadata", "true")

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        // handle err
    }

    if resp.StatusCode == http.StatusOK {
        respBytes, _ := ioutil.ReadAll(resp.Body)
        var access_token_resp map[string]interface{}
        json.Unmarshal(respBytes, &access_token_resp)
        access_token, _ := access_token_resp["access_token"].(string)
        
        // Get Passsword
        var bearer_token = "Bearer " + access_token
        var document_db_api = "https://management.azure.com/subscriptions/eec8e14e-b47d-40d9-8bd9-23ff5c381b40/resourceGroups/sfbpdeployrg/providers/Microsoft.DocumentDB/databaseAccounts/" + username + "/listKeys?api-version=2016-03-31"
        req_keys, err := http.NewRequest("POST",document_db_api, nil)
        req_keys.Header.Set("Authorization", bearer_token)
        if err != nil {
           // handle err
        }

        resp_keys, err := http.DefaultClient.Do(req_keys)
        if err != nil {
            // handle err
        }
        respBytes_keys, _ := ioutil.ReadAll(resp_keys.Body)
        var cosmos_listkeys_resp map[string]interface{}
        json.Unmarshal(respBytes_keys, &cosmos_listkeys_resp)
        password, _ := cosmos_listkeys_resp["primaryMasterKey"].(string)
    }
}

func insert(w http.ResponseWriter, r *http.Request, session *mgo.Session) {
  if r.Method == "GET" {
    t, _ := template.ParseFiles("insert.html")
	t.Execute(w, nil)
  } else {
    r.ParseForm()
	
	name := r.Form["Name"][0]
	number := r.Form["Number"][0]
	description := r.Form["Description"][0]
	count := r.Form["Count"][0]
	
	insertDocument(name, number, description, count, session);
	
	http.ServeFile(w, r, "insert.html")
  }
}

func insertDocument(name string, number string, description string, count string, session *mgo.Session) {
	// get collection
	collection := session.DB(database).C("package")

	// insert Document in collection
	err := collection.Insert(&Package{
		Name:        name,
		Number:      number,
		Description: description,
		Count:       count,
	})

	if err != nil {
		log.Fatal("Problem inserting data: ", err)
		return
	}
}
	
// Package represents a document in the collection
type Package struct {
	Id          bson.ObjectId `bson:"_id,omitempty"`
	Name        string
	Number      string
	Description string
	Count       string
}

func main() {
	// DialInfo holds options for establishing a session with a MongoDB cluster.
	dialInfo := &mgo.DialInfo{
		Addrs:    []string{fmt.Sprintf("%s.documents.azure.com:10255", database)}, // Get HOST + PORT
		Timeout:  60 * time.Second,
		Database: database, // Database Name
		Username: username, // DB Username
		Password: password, // DB Password
		DialServer: func(addr *mgo.ServerAddr) (net.Conn, error) {
			return tls.Dial("tcp", addr.String(), &tls.Config{})
		},
	}

	// Create a session which maintains a pool of socket connections
	// to our MongoDB.
	session, err := mgo.DialWithInfo(dialInfo)

	if err != nil {
		fmt.Printf("Can't connect to mongo, go error %v\n", err)
		os.Exit(1)
	}

	defer session.Close()

	// SetSafe changes the session safety mode.
	// If the safe parameter is nil, the session is put in unsafe mode, and writes become fire-and-forget,
	// without error checking. The unsafe mode is faster since operations won't hold on waiting for a confirmation.
	// http://godoc.org/labix.org/v2/mgo#Session.SetMode.
	session.SetSafe(&mgo.Safe{})
	
	// This handler listeners for the form, and passes it to the insert func handler
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		insert(w, r, session)
	})
	
	http.ListenAndServe(port, nil)
}
