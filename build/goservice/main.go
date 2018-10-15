package main

import (
	"crypto/tls"
	"fmt"
	"log"
	"net"
	"os"
	"time"
    "html/template"
	"net/http"
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
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
	password = os.Getenv("DB_PASSWORD")
	port = 80
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
